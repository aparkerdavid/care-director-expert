# Setup

```sh
git clone git@github.com:aparkerdavid/care-director-expert.git
cd care-director-expert
mkdir documents
```
if you don't have podman installed on your system, do so. (podman is equivalent to docker, but somewhat less annoying)

```sh
brew install podman
```

add any documents you'd like to ingest to the `documents` directory, and any code repositories to the `code` directory. then run

```sh
./seed.sh
```

# Use with Claude Desktop

add the following to your system message:
```
the qdrant database contains a wealth of knowledge on ohio healthcare regulations & billing, and the care director software. always search qdrant for relevant info before answering a question. include the file paths of any qdrant database results in your response.
```

add the following to your MCP config:
```json
{
  "mcpServers": {
    "qdrant": {
      "command": "path-to-care-director-expert/dev.sh",
      "cwd": "path-to-care-director-expert"
    }
  }
}
```
