package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"net/http"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
	"github.com/golang/protobuf/ptypes"
	"os"
	"mime/multipart"
	"bytes"
	"io"
)

type SmartContract struct {
	contractapi.Contract
}

type DataProcessingSpec struct {
	MRENCLAVE string `json:"MRENCLAVE"`
	Date	  string `json:"Date"`
	Input     string `json:"Input"`
	Output    string `json:"Output"`
	Functions string `json:"CalledFunctions"`
}

type AnalyzerResponse struct {
	Result string `json:"Result"`
	ProcessingSpec struct {
		Input     []string `json:"Input"`
		Functions []string `json:"Functions"`
		Output    []string `json:"Output"`
	} `json:"ProcessingSpec"`
}

const GRAMINEADDR string = "http://gramine-container:8008"
const VERIFYADDR string = "http://analysis-container:8009"

// RegisterProgram issues a new program info to the world state with given details.
func (s *SmartContract) RegisterProgram(ctx contractapi.TransactionContextInterface, program string, SPID string, isLinkable string) (string, error) {
	programPath := "/tmp/program.py"
	// file write
	file, err := os.Create(programPath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	file.Write([]byte(program))

	// obtain MRENCLAVE
	PROGRAM_MRENCLAVE, err := GetMRENCLAVE(programPath, SPID, isLinkable)
	if err != nil {
		return "", err
	}
	if PROGRAM_MRENCLAVE == "" {
		return "", fmt.Errorf("Cannot get MRENCLAVE.")
	}

	// verify the program
	result, input, output, functions, err := VerifyProgram(programPath)
	if err != nil {
		return "", err
	}
	if result == "NG" {
		return "", fmt.Errorf("A data leak has been detected.")
	}

	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return "", err
	}
	timestamp, err := ptypes.Timestamp(txTimestamp)
	if err != nil {
		return "", err
	}

	processingSpec := DataProcessingSpec{MRENCLAVE: PROGRAM_MRENCLAVE, Date: timestamp.Format("2006-01-02 15:04:05"), Input: input, Output: output, Functions: functions}

	specJSON, err := json.Marshal(processingSpec)
	if err != nil {
		return "", err
	}

	ctx.GetStub().PutState(PROGRAM_MRENCLAVE, specJSON)
	return "AppID(MRENCLAVE): " + PROGRAM_MRENCLAVE + "\n" + "Input: " + input + "\n" + "Output: " + output + "\n", nil
}

func (s *SmartContract) GetProcessingSpec(ctx contractapi.TransactionContextInterface, MRENCLAVE string) (*DataProcessingSpec, error) {
	programInfoJSON, err := ctx.GetStub().GetState(MRENCLAVE)
	if err != nil {
	return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if programInfoJSON == nil {
	return nil, fmt.Errorf("the asset %s does not exist", MRENCLAVE)
	}

	var processingSpec DataProcessingSpec
	err = json.Unmarshal(programInfoJSON, &processingSpec)
	if err != nil {
	return nil, err
	}

	return &processingSpec, nil
}

func (s *SmartContract) GetAllProcessingSpec(ctx contractapi.TransactionContextInterface) ([]*DataProcessingSpec, error) {
	// range query with empty string for startKey and endKey does an
	// open-ended query of all assets in the chaincode namespace.
	resultsIterator, err := ctx.GetStub().GetStateByRange("", "")
	if err != nil {
		return nil, err
	}
	defer resultsIterator.Close()

	var processingSpecArr []*DataProcessingSpec
	for resultsIterator.HasNext() {
	queryResponse, err := resultsIterator.Next()
	if err != nil {
		return nil, err
	}

	var processingSpec DataProcessingSpec
	err = json.Unmarshal(queryResponse.Value, &processingSpec)
	if err != nil {
	return nil, err
	}
	processingSpecArr = append(processingSpecArr, &processingSpec)
	}

	return processingSpecArr, nil
}

func (s *SmartContract) RevokeProcessingSpec(ctx contractapi.TransactionContextInterface, MRENCLAVE string) error {
	exists, err := s.ProcessingSpecExists(ctx, MRENCLAVE)
	if err != nil {
	return err
	}
	if !exists {
	return fmt.Errorf("Data processing specification %s does not exist", MRENCLAVE)
	}

	return ctx.GetStub().DelState(MRENCLAVE)
}

func (s *SmartContract) ProcessingSpecExists(ctx contractapi.TransactionContextInterface, MRENCLAVE string) (bool, error) {
	programInfoJSON, err := ctx.GetStub().GetState(MRENCLAVE)
	if err != nil {
	return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return programInfoJSON != nil, nil
}

func GetMRENCLAVE(filepath string, SPID string, isLinkable string) (string, error) {
	// obtain MRENCLAVE of the program
	file, err := os.Open(filepath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	reqBody := &bytes.Buffer{}

	// file
	writer := multipart.NewWriter(reqBody)
	
	part, err := writer.CreateFormFile("program", filepath)
	if err != nil {
		return "", err
	}
	_, err = io.Copy(part, file)
	if err != nil {
		return "", err
	}

	// SPID, isLinkable
	part, err = writer.CreateFormField("SPID")
	if err != nil {
		return "", err
	}
	if _, err = part.Write([]byte(SPID)); err != nil {
		return "", err
	}

	part, err = writer.CreateFormField("isLinkable")
	if err != nil {
		return "", err
	}
	if _, err = part.Write([]byte(isLinkable)); err != nil {
		return "", err
	}

	contentType := writer.FormDataContentType()
	writer.Close()

	res, err := http.Post(GRAMINEADDR + "/upload", contentType, reqBody)
	if err != nil {
		return "", err
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return "", err
	}
	MRENCLAVE := string(body)
	return MRENCLAVE[:len(MRENCLAVE)-1], nil
}

func VerifyProgram(filepath string) (string, string, string, string, error) {
	file, err := os.Open(filepath)
	if err != nil {
		return "NG", "", "", "", err
	}
	defer file.Close()

	reqBody := &bytes.Buffer{}

	// file
	writer := multipart.NewWriter(reqBody)
	
	part, err := writer.CreateFormFile("file", filepath)
	if err != nil {
		return "NG", "", "", "", err
	}
	_, err = io.Copy(part, file)
	if err != nil {
		return "NG", "", "", "", err
	}

	contentType := writer.FormDataContentType()
	writer.Close()
	
	res, err := http.Post(VERIFYADDR + "/verify", contentType, reqBody)
	if err != nil {
		return "NG", "", "", "", err
	}
	if res.StatusCode == 400 {
		return "NG", "", "", "", fmt.Errorf("Analysis server: 400 Bad Request")
	}

	body, err := io.ReadAll(res.Body)
	if err != nil {
		return "NG", "", "", "", err
	}

	var result AnalyzerResponse
	if err = json.Unmarshal(body, &result); err != nil {
		return "NG", "", "", "", err
	}
	
	if result.Result == "NG" {
		return "NG", "", "", "", nil
	}
	
	return result.Result, strings.Join(result.ProcessingSpec.Input, ", "), strings.Join(result.ProcessingSpec.Output, ", "), strings.Join(result.ProcessingSpec.Functions, ", "), nil
}
