1. Install
   - [General info for all platforms](https://github.com/ollama/ollama#ollama)
   - macOS better option: `brew install ollama`
2. Start server `ollama start`
3. Serve some model (e.g. `phi3 mini`) in terminal chat
4. Connecting to it with OpenAI API (drop-in replacement):
    ```python
    from openai import OpenAI
    
    client = OpenAI(
        base_url='http://localhost:11434/v1/',
        api_key='ollama',
    )
    ```
5. Serving ollama inside Docker container
    1. Run ollama inside Docker
        ```bash
        docker run -it \
            -v ollama:/root/.ollama \
            -p 11434:11434 \
            --name ollama \
            ollama/ollama
        ```
    2. Pull the model
        ```bash
        docker exec -it ollama bash # enter docker container with ollama
        ollama pull phi3
        ```
       
Misc
- get version of the ollama client:
```bash
docker exec -it ollama bash # enter docker container with ollama
ollama -v
```