<<<<<<< 0f7cb59ed65770f4ee59992a7c20d5ee136ff41e
## Cloudify ARIA Extensions

This repository provides ARIA with support for running Cloudify-based plugins.
Using an adapter that serves as a translation layer between the Cloudify and ARIA APIs, ARIA is able to make use of plugins that were designed to work with Cloudify.
### Installation

1. clone the repository

`git clone https://github.com/cloudify-cosmo/aria-extension-cloudify.git`

2. install the requirements:

`pip install -r requirements.txt`

3. install Cloudify ARIA extensions. This installs the adapter, and it should be done in the same environment in which ARIA is installed:

`pip install .`


4. (optional, for developing purposes) install the test requirements:

`pip install -r aria_extension_tests/requirements.txt`

Using the adapter, ARIA is expected to support any Cloudify plugin. However, depending on their implementation, some plugins may not work out-of-the-box with ARIA, and small adapter modifications may be need.

Specifically, The [Cloudify AWS Plugin](https://github.com/cloudify-cosmo/cloudify-aws-plugin) 1.4.10 and the [Cloudify Openstack Plugin](https://github.com/cloudify-cosmo/cloudify-openstack-plugin) 2.0.1 were explicitly translated and tested using the adapter. Newer versions are expected to work as well.

#### Installing a plugin
In order to use any Cloudify plugin, you'll need to install it using a `.wgn` ([wagon](https://github.com/cloudify-cosmo/wagon)) file. For CentOS or RHEL, you can obtain the plugin `.wgn` from the [Cloudify plugin downloads page](http://cloudify.co/downloads/plugin-packages.html).

After obtaining the `.wgn`, you can install the plugin:

`aria plugins install <path to .wgn>`

Another, more generic way, of obtaining a plugin `.wgn` is to create it from source. Here's an example, using the AWS plugin:

1. clone/download the Cloudify AWS Plugin:

`git clone https://github.com/cloudify-cosmo/cloudify-aws-plugin.git`

2. (optional) if you want to install a specific version of the plugin, checkout the corresponding tag.

`git checkout <version number>`

3. create a `.wgn` file from the repository:

`wagon create <path to plugin repository>`
=======
### ARIA Demo for AT&T
Use an empty directory, on a fresh virtual environment:

#### Installing ARIA

1. Clone the aria repo:

`git clone https://github.com/apache/incubator-ariatosca.git`

2. Enter the cloned directory:

`cd incubator-ariatosca`

3. Install the requirements:

`pip install -r requirements.txt`

4. Install aria:

`pip install .`

#### Running the local hello world example
5. Enter the hello world example directory:

`cd examples/hello-world`

6. Store the local hello world service template:

`aria service-templates store helloworld.yaml local`

7. Create a service from the stored service template:

`aria services create -t local local`

8. Run the install workflow on the created service:

`aria executions start install -s local -vvv`

#### Installing ARIA ssh capabilities
9. Go back to the incubator-ariatosca directory.

`cd ../..`

10. Install aria ssh capabilities:

`pip install .[ssh]`

#### Installing the cloudify AWS plugin
11. go back to the top level directory:

`cd ..`

12. Clone the cloudify-aws-plugin repo

`git clone https://github.com/cloudify-cosmo/cloudify-aws-plugin.git`

13. Enter the cloned directory:

`cd cloudify-aws-plugin`

14. Checkout tag 1.4.10

`git checkout 1.4.10`

15. Go back to the top level directory:

`cd ..`

16. Create the aws plugin wagon:

`wagon create cloudify-aws-plugin/`

17. Install the wagon plugin:

`aria plugins install <path_to_wagon>`

#### Install the cloudify aria extensions
18. Clone the cloudify-aria-extensions repo:

`git clone https://github.com/cloudify-cosmo/cloudify-aria-extensions.git`

19. Enter the cloned directory:

`cd cloudify-aria-extensions`

20. Checkout the aria-demo branch:

`git checkout aria-demo`

21. Install cloudify-aria-extensions:

`pip install .`

#### Running the AWS hello world example
22. Enter the hello world example directory:

`cd examples/aws-hello-world/`

23. Store the service template:

`aria service-templates store aws-helloworld.yaml aws`

24. Create a service from the stored service template:

`aria services create -t aws aws -i inputs.yaml`

25. Run the install workflow on the created service:

`aria executions start install -s aws -vvv`
>>>>>>> Aria demo
