import imp
import sys
import os

## find and load the conf file
this_dir = os.path.dirname(sys.argv[0])
conf_path = os.path.join(os.path.dirname(this_dir),'conf.py')
conf = imp.load_source('conf',conf_path)

## create all necessary app paths
package_root = conf.PACKAGE_ROOT
source_data = os.path.join(package_root,'source_data')
auth_dir = os.path.join(source_data,'concepts','authority_files')
graph_dir = os.path.join(source_data,'resource_graphs')
business_dir = os.path.join(source_data,'business_data')

## other
log_dir = os.path.join(this_dir,'logs')
concept_scheme_name = conf.CONCEPT_SCHEME_NAME

