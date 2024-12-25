package main

import (
	"encoding/json"
	"fmt"
	"net/http"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/hyperledger/fabric-chaincode-go/pkg/cid"
	"github.com/golang/protobuf/ptypes"
	"os"
	"mime/multipart"
	"bytes"
	"io"
)

type SmartContract struct {
	contractapi.Contract
}

type LibraryFunc struct {
	Func string `json:"Func"`
	Date	  string `json:"Date"`
	Status string `json:"Status"`
	IsApproved map[string]bool `json:"IsApproved"`
	DateAccepted string `json:"DateAccepted"`
}

var Participants []string

func (s *SmartContract) RegisterID(ctx contractapi.TransactionContextInterface) error {
	id, err := cid.GetMSPID(ctx.GetStub())
	if err != nil {
		return err
	}
	Participants = append(Participants, id)
	return nil
}

const GRAMINEADDR string = "http://gramine-container:8008"
const VERIFYADDR string = "http://analysis-container:8009"

func (s *SmartContract) SuggestFunc(ctx contractapi.TransactionContextInterface, functionName string, function string) error {

	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return err
	}
	timestamp, err := ptypes.Timestamp(txTimestamp)
	if err != nil {
		return err
	}

	m := make(map[string]bool)
	for _, participant := range Participants {
		m[participant] = false
	}

	libraryFunc := LibraryFunc{Func: function, Date: timestamp.Format("2006-01-02 15:04:05"), Status: "Pending", IsApproved: m, DateAccepted: ""}

	libJSON, err := json.Marshal(libraryFunc)
	if err != nil {
		return err
	}
	if libJSON == nil {
		return fmt.Errorf("failed to marshal json\n")
	}
	return ctx.GetStub().PutState(functionName, libJSON)
}

func (s *SmartContract) Vote(ctx contractapi.TransactionContextInterface, functionName string, isApproved int) (string, error) {

	libraryFuncJSON, err := ctx.GetStub().GetState(functionName)
	if err != nil {
		return "", fmt.Errorf("failed to read from world state: %v", err)
	}
	if libraryFuncJSON == nil {
		return "", fmt.Errorf("failed to get function\n")
	}

	var libraryFunc LibraryFunc
	err = json.Unmarshal(libraryFuncJSON, &libraryFunc)
	if err != nil {
		return "", err
	}
	
	var newLibraryFunc LibraryFunc
	
	if (libraryFunc.Status == "Rejected") {
		return "", fmt.Errorf("This function is already rejected\n")
	}

	if (isApproved == 1) {
		id, err := cid.GetMSPID(ctx.GetStub())
		if err != nil {
			return "", err
		}
		libraryFunc.IsApproved[id] = true
		newLibraryFunc = LibraryFunc{Func: libraryFunc.Func, Date: libraryFunc.Date, Status: libraryFunc.Status, IsApproved: libraryFunc.IsApproved, DateAccepted: ""}
	} else {
		newLibraryFunc = LibraryFunc{Func: libraryFunc.Func, Date: libraryFunc.Date, Status: "Rejected", IsApproved: libraryFunc.IsApproved, DateAccepted: ""}
	}
	
	count := 0
	if (newLibraryFunc.Status != "Rejected") {
		for _, isApproved := range newLibraryFunc.IsApproved {
			if !isApproved {
				break
			}
			count++
			if (count == len(newLibraryFunc.IsApproved)) {
				// update status
				newLibraryFunc.Status = "Accepted"

				// set DateAccepted
				txTimestamp, err := ctx.GetStub().GetTxTimestamp()
				if err != nil {
					return "", err
				}
				timestamp, err := ptypes.Timestamp(txTimestamp)
				if err != nil {
					return "", err
				}

				newLibraryFunc.DateAccepted = timestamp.Format("2006-01-02 15:04:05")
			}
		}
	}

	// put
	libJSON, err := json.Marshal(newLibraryFunc)
	if err != nil {
		return "", err
	}
	return fmt.Sprintf("Status: %s\n", newLibraryFunc.Status), ctx.GetStub().PutState(functionName, libJSON)
}

func (s *SmartContract) UpdateLib(ctx contractapi.TransactionContextInterface) error {
	suggestedFunc, err := GetSuggestedFunc(ctx)
	if err != nil {
		return nil
	}
	var acceptedFunc string
	for _, funcInfo := range suggestedFunc {
		if (funcInfo.Status == "Accepted") {
			acceptedFunc += funcInfo.Func
		}
	}

	// install the updated file to the servers
	libPath := "/tmp/plib.py"
	file, err := os.Create(libPath)
	if err != nil {
		return err
	}
	defer file.Close()
	file.Write([]byte(acceptedFunc))
	
	var address[2] string = [2]string {GRAMINEADDR, VERIFYADDR}

	for _, addr := range address {
		file, err = os.Open(libPath)
		if err != nil {
			return err
		}
		defer file.Close()
		
		reqBody := &bytes.Buffer{}
		writer := multipart.NewWriter(reqBody)
		part, err := writer.CreateFormFile("lib", libPath)
		if err != nil {
			return err
		}
		_, err = io.Copy(part, file)
		if err != nil {
			return err
		}
		writer.Close()
	
		contentType := writer.FormDataContentType()
	
		res, err := http.Post(addr + "/update", contentType, reqBody)
	
		if err != nil {
			return err
		}
		body, err := io.ReadAll(res.Body)
		if err != nil {
			return err
		}
		fmt.Println(string(body))
		if ((string(body) != "Updated") && (string(body) != "\"Updated\"")) {
			return fmt.Errorf("Error\n")
		}
	}
	return nil
}

func (s *SmartContract) GetCurrentLib(ctx contractapi.TransactionContextInterface) (string, error) {

	suggestedFunc, err := GetSuggestedFunc(ctx)
	if err != nil {
		return "", err
	}
	
	var acceptedFunc string
	for _, funcInfo := range suggestedFunc {
		if (funcInfo.Status == "Accepted") {
			acceptedFunc += funcInfo.Func
		}
	}
	return acceptedFunc, nil
}

func (s *SmartContract) ReadSuggestedFunc(ctx contractapi.TransactionContextInterface) ([]*LibraryFunc, error) {
	return GetSuggestedFunc(ctx)
}

func GetSuggestedFunc(ctx contractapi.TransactionContextInterface) ([]*LibraryFunc, error) {
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var suggestedFunc []*LibraryFunc
	for resultsIterator.HasNext() {
		queryResponse, err := resultsIterator.Next()
		if err != nil {
			return nil, err
		}

		var funcInfo LibraryFunc
		err = json.Unmarshal(queryResponse.Value, &funcInfo)
		if err != nil {
			return nil, err
		}
		suggestedFunc = append(suggestedFunc, &funcInfo)
	}

	return suggestedFunc, nil
}
