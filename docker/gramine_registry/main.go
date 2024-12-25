package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"log"
	"io"
)

func upload(web http.ResponseWriter, req *http.Request) {

	log.Printf("%21s - %4s %s", req.RemoteAddr, req.Method, req.URL.Path)

	switch req.Method {
		case "POST":
			file, _, _ := req.FormFile("program")
			if file == nil {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "Program not sent")
				return
			}
			out, _ := os.Create("/upload/main.py")
			io.Copy(out, file)

			SPID := req.Form.Get("SPID")
			if SPID == "" {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "SPID not specified")
				return
			}

			isLinkable := req.Form.Get("isLinkable")
			if isLinkable == "" {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "isLinkable not specified")
				return
			}
			
			log.Printf("Start building")
			MRENCLAVE, err := exec.Command("./../build.sh", SPID, isLinkable).Output()
			log.Printf("Finish buiding")

			if err != nil {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "Cannot get MRENCLAVE")
				return
			}

			web.WriteHeader(http.StatusOK)
			fmt.Fprint(web, string(MRENCLAVE))

		default:
			web.WriteHeader(http.StatusMethodNotAllowed)
			fmt.Fprint(web, "Method not allowed.\n")
    }
}

func update(web http.ResponseWriter, req *http.Request) {
	
	log.Printf("%21s - %4s %s", req.RemoteAddr, req.Method, req.URL.Path)

	switch req.Method {
		case "POST":
			file, _, _ := req.FormFile("lib")
			if file == nil {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "Code not sent")
				return
			}

			lib, err := os.OpenFile("/root/code/plib.py", os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0666)
			if err != nil {
				fmt.Fprint(web, "Cannot open library")
				return
			}
			defer lib.Close()
			io.Copy(lib, file)

			web.WriteHeader(http.StatusOK)
			fmt.Fprint(web, "Updated")
		default:
			web.WriteHeader(http.StatusMethodNotAllowed)
			fmt.Fprint(web, "Method not allowed.\n")
	}
}

func updateFilters(web http.ResponseWriter, req *http.Request) {
	
	log.Printf("%21s - %4s %s", req.RemoteAddr, req.Method, req.URL.Path)

	switch req.Method {
		case "POST":
			file, _, _ := req.FormFile("filters")
			if file == nil {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "Code not sent")
				return
			}

			lib, err := os.OpenFile("/root/code/filters.py", os.O_WRONLY|os.O_CREATE|os.O_TRUNC, 0666)
			if err != nil {
				fmt.Fprint(web, "Cannot open library")
				return
			}
			defer lib.Close()
			io.Copy(lib, file)

			web.WriteHeader(http.StatusOK)
			fmt.Fprint(web, "Updated")
		default:
			web.WriteHeader(http.StatusMethodNotAllowed)
			fmt.Fprint(web, "Method not allowed.\n")
	}
}

func main() {
	log.Printf("Started gramine server prosess\n")
	http.HandleFunc("/upload", upload)
	http.HandleFunc("/update", update)
	http.HandleFunc("/updateFilters", updateFilters)
	http.ListenAndServe(":8008", nil)
}
