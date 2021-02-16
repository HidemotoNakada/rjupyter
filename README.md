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
- --group_id GROUP_ID  ( for ABCI )
- --resource_type TYPE ( for ABCI )
- --use_qrsh            
