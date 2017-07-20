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
