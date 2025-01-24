# µBench Service cell

Adapted excerpt from the [µBench repository](https://github.com/mSvcBench/muBench)

The software that implements a service-cell is `CellController-mp.py`, which exposes REST/HTTP  and gRPC APIs. After that a request is received, it uses other libraries to run the internal service (`InternalServiceExecutor.py`) and, then, the external services (`ExternalServiceExecutor.py`). 

`CellController-mp.py` uses Gunicorn WSGI for implementing the HTTP/REST API. HTTP requests are served by a pool of processes and threads according to the `workers` and `threads` keys in `workmodel.json`. Therefore, a service-cell at most uses a number of CPU cores equal to `workers`. In the case of gPRG, `CellController-mp.py` uses only one core (single worker). So multi-process experiments can only be performed using the REST request method.

## Why adapt?

This adaption provides better handling within Kubernetes, as it improves logging (to stdout/stderr) and runs the service cell as main process, which allows Kubernetes to detect failures and restart the pods.

Automatic docker build+publish via github actions ensuring consistency across updates.

Also provides a local docker-compose variant, mounting necessary files and parameters to test a cell locally.

    docker-compose up -d
    docker-compose logs

### Example CURL

Simple GET request

    curl http://localhost/api/v1
  
Simple POST request to test the `trace` variant.

    curl --header "Content-Type: application/json" --request POST --data "{\"ms-500\":[{}]}" http://localhost/api/v1

