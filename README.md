# blocky-web
A super basic web interface to the blocky-web DNS sinkhole

## Installation
### Python Installations
```sh
poetry install
```

### Front-End
```sh
npm install
npm run build
```

### Docker
```sh
docker run -v $PWD/config.yaml:/config/config.yaml -v $PWD/allowed.txt:/config/allowed.txt -p 80:80 --ti cazier/blockyweb:latest
```
