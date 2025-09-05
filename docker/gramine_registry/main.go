package main

import (
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strings"
	"time"
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

			log.Printf("Start building (SPID:%s, isLinkable:%s)", string(SPID), string(isLinkable))
			start := time.Now()
			mrenclave_bytes, err := exec.Command("./../build.sh", SPID, isLinkable).Output()
			end := time.Now()
			mrenclave := strings.TrimRight(string(mrenclave_bytes), "\r\n")
			log.Printf("Finish building (MRENCLAVE:%s)", mrenclave)

			if err != nil {
				web.WriteHeader(http.StatusBadRequest)
				fmt.Fprint(web, "Cannot get MRENCLAVE")
				return
			}

			duration := end.Sub(start)

			fmt.Printf("___BENCH___ MRENCLAVE retrieval (Start:%s, End:%s, Duration_ms:%d)\n", start.Format("2006-01-02 15:04:05"), end.Format("2006-01-02 15:04:05"), duration.Milliseconds())

			log.Printf("MRENCLAVE: %s", mrenclave)

			web.WriteHeader(http.StatusOK)
			fmt.Fprint(web, mrenclave)

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
	log.Printf("Started gramine server process\n")
	http.HandleFunc("/upload", upload)
	http.HandleFunc("/update", update)
	http.HandleFunc("/updateFilters", updateFilters)
	http.ListenAndServe(":8008", nil)
}
