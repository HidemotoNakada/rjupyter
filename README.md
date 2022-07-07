# rjupyter
invokes jupyter notebook remotely

## prerequistie
- install jupyter notebook on the server side.
 + make sure it can be invoked with 'jupyter notebook' 

## usage
- clone the code on both of the client and server.
- set up PATH so that the server side script is in the path.
 + you need to setup the PATH in .zshenv or .bash_profile, since .zshrc or .bashrc might not evaluated by ssd.
- call the script
```
> python rjupyter_client.py SERVER
```

### options
- --cwd TARGET_DIRECTORY
- --server_command SERVER_SIDE_SCRIPT_PATH
- --push_server_code
    if specified push the server code.
    In this case, you do not need to checkout on the server side
- --group_id GROUP_ID  ( for ABCI )
- --resource_type TYPE ( for ABCI )
- --use_qrsh            


### example

```
python rjupyter_client.py --use_qrsh --push_server_code --group_id xxxx --resource_type rt_C.small abci
```
