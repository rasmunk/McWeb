# Dockerised McWeb

This repository is a version of McWeb, running within a Docker container, and able to schedule remote processing of McStas and McXtrace processing. 

By default McWeb is accessible at 127.0.0.1:80. If required, an nginx reverse proxy is included though is not used by default. McWeb itself can be configured at 'McWeb/nginx/mcweb.conf'.

Note that a default django superuser is created during the McWeb docker image construction. This can be configured using the variables 'DJANGO_PASSWORD', 'DJANGO_USER' and 'DJANGO_EMAIL' within 'McWeb/Dockerfile'.

# Running the stack

To run McWeb, run the following command within the McWeb directory:
* docker stack deploy --compose-file docker-compose.yaml mcweb-service

This is sufficient for testing but should not be used in deployed systems as it contains default django logins as discussed below. These should be altered in the Dockerfile. If you wish to host McWeb and have it accessible from an external IP you will need to add said IP to the ALLOWED_HOSTS list in 'McWeb/mcsimrunner/mcweb/settings.py.in'. Once any edits have been made you can build your image with the command:
* docker build -f Dockerfile --no-cache --tag UNIQUE-IMAGE-NAME-HERE .

This will build a local copy of the 'mcweb' docker image. Once 'docker-compose.yaml' has been updated with the new image name, it can then be run using:
* docker stack deploy --compose-file docker-compose.yaml mcweb-service

Once these commands have run you should see 1 docker image running with a name such as 'mcweb-service_mcweb.1.xp0dznz29ykw1b8vfg30c1whw'. Note that the exact name will differ each time the stack is deployed, and that it may take a few moments to start.

# Stopping the stack

To stop the docker stack run the command:
* docker stack rm mcweb-service

Note, this may take several moments to remove the McWeb container.

# Accessing McWeb

On the host machine you can now access McWeb through an internet browser by navigating to '127.0.0.1:80', assuming you did not modify 'McWeb/nginx/nginx-proxy.conf', or 'McWeb/mcsimrunner/mcweb/settings.py.in'.

If everything has hosted correctly you will be greeted with a login screen, you can login as the superuser defined in 'McWeb/Dockerfile'. By default this is 'djangoadmin' with password 'Passw0rd123'. This should obviously be changed for any deployment implementation.

You should then be taken to a start screen displaying the 'SANSsimple' instrument which can be run as per any other McWeb deployment. This is the default landing page, so you should not delete the SANSsimple.instr.

# Configuring remote processing

This McWeb deployment uses the python package 'corc' (https://pypi.org/project/corc/) to schedule processing on remote resources. To do so necessary configurations will need to be defined by a user. Currently this is done outside of the docker container, with the relevant configs mounted from the .aws, .corc, and.oci directories within configs-platform. Brief READMEs are included in each directory explaining their role. Different configs may be mounted, though docker-compose.yaml will need to be altered accordingly.

# Adding instrument and component definitions

To add additional instrument definitions to McWeb they can be added to the 'McWeb/bootstrap_data/instruments' directory. Note that the 'bootstrap_data' folder and its contents MUST be owned by the user 'www-data'. This is as it is used by McWeb internally, running as www-data. Any files not owned by www-data will not be added to the McWeb interface, and may crash the system.

Instruments added here should be sorted into groups for ease of use. The default group is 'intro-ns'. Any new instruments or groups can be added here, along with any supporting files or components alongside the relevant instrument file. This is as this directory is mounted into the McWeb container and is the source for instrument files used to construct the McWeb interface. Note that it may take up to 10 minutes from creating a new instrument here for it to appear in McWeb.

Do not delete the 'intro-ns' group directory, or the 'SANSsimple.instr' file within it as this is the default landing instrument for the McWeb interface.

# Retrieving Data in McWeb

The directory 'McWeb/bootstrap_data/simrun_data' is also mounted to the McWeb docker container. This is the directory that any output is written to by the McStas/McXtrace processing. This also means that any data produced is retained beyond the life of the docker container, and can easily be retrieved from it. 

If the system has been set up using corc to schedule remote processing, it will also be available in whatever remote storage has been defined and should be manually deleted.

# Additional options in McWeb

A few small additions have been made to this implementation of McWeb. 

A toggle option has been added to the Runtime configuration for remote processing. This will schedule the simulation processing within an external cloud infrastructure, as defined by 'configs-platform/.corc/config'.

Related to the remote processing, additional options for copying additional files to the remote processing have been added. Users can either define all additional files required for a simulation run within a text field, or can mark that all non-.instr and non-.comp file in the instrument group directory will be copied accross.

# McWeb

* Base repo: https://github.com/McStasMcXtrace/McWeb
* For documentation go to our Wiki: https://github.com/McStasMcXtrace/McWeb/wiki
* For issues and tasks go to our issue list: https://github.com/McStasMcXtrace/McWeb/issues
