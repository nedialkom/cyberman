# cyberman
Automated platform for success

## deployment

To deploy this project execute the following steps:

1. make sure you have the prerequisites:
```bash
docker --version
docker compose version
git --version
```
If you do not have running docker you may install Docker desktop:
1.1 For macOS (Apple Silicon/Intel)
```bash
brew install --cask docker
open -a Docker
brew install git
```
1.2. For Ubuntu/Linux
```bash
sudo apt update
wget https://desktop.docker.com/linux/main/amd64/docker-desktop-<version>-amd64.deb
sudo apt install ./docker-desktop-<version>-amd64.deb
systemctl --user start docker-desktop
docker-desktop
sudo apt install git
```
1.3. For Windows (PowerShell)
```bash
winget install --id Docker.DockerDesktop -e
winget install --id Git.Git -e --source winget

```
2. Download the software
```bash
  git clone https://github.com/nedialkom/cyberman.git
```
## Run it
Before running it you need some input from me, you may contact me on 
[nedialkom@gmail.com](mailto:nedialkom@gmail.com?subject=[GitHub]%20cyberman)
```bash
cd cyberman
docker-compose up --build
```
