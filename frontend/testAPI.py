import requests
server = "http://127.0.0.1:5000"


if __name__ == "__main__":
    r = requests.get('%s/search/file/download?id=dedewdwedew' %(server))
    print(r,r.json())