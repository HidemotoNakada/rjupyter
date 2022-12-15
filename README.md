# rjupyter

Rjupyter invokes jupyter notebook on the remote node and automatically forward the port using ssh tunneling. You do not need to install stub on the server side, since it will be automatically shiped as an argument. 

It supports [ABCI](https://abci.ai). It will allocate a node using qrsh and launch jupyter on the node.


## Prerequistie
- install jupyter notebook on the server side.
    - make sure it can be invoked with 'jupyter notebook' 
    - make sure it is available for non-intaractive shell. '.bashrc' might have lines like
    ```
    # If not running interactively, don't do anything
    case $- in
        *i*) ;;
          *) return;;
    esac
    ```
    In that case, your python/jupyter configuration have to be *above* these lines.

## Usage
- clone the code on both of the client.
- call the script
    ```
    > python rjupyter_client.py SERVER
    ```

## Options
- --cwd TARGET_DIRECTORY
- --server_command SERVER_SIDE_SCRIPT_PATH
- --use_server_side_code

    Mainly for debbugging. 

    If specified use the server code on the server.
    In this case, you need to checkout also on the server side
    and set up PATH so that the server side script is in the path.

- --group_id GROUP_ID  ( for ABCI )
- --resource_type TYPE ( for ABCI )
- --use_qrsh           ( for ABCI ) 
- --num_nodes          ( for ABCI )
- --duration "XX:XX:XX"( for ABCI )


## example
- for usual linux server
    ```
    python rjupyter_client.py sss
    ```

- for ABCI
    ```
    python rjupyter_client.py --use_qrsh --group_id xxxx --resource_type rt_C.small abci
    ```
