# To find the latency 
curl -o /dev/null -s -w "DNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTLS: %{time_appconnect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" https://abcd.net


curl -o /dev/null -s -w "Total: %{time_total}s\n" https://abcd.com

## Python
import time
import requests

url = "https://example.com"
start = time.perf_counter()
response = requests.get(url)
end = time.perf_counter()

print(f"Status: {response.status_code}, Latency: {(end - start) * 1000:.2f} ms")


## If you want averages & percentiles over many requests:
Install hey (Go-based load tester):

hey -n 100 https://example.com

OR use Apache Benchmark:

ab -n 100 https://example.com/

## curl in while loop
for i in {1..100}; do
  curl -o /dev/null -s -w "%{time_total}\n" https://example.com
done

##
