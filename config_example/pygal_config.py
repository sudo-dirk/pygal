import os
import urllib

basepath = os.path.abspath(os.path.dirname(__file__))


################################################################
# Developer stuff (change only if you know what you are doing) #
################################################################
DEBUG = False                                                  #
################################################################

######################################################################################
# Administration stuff                                                               #
######################################################################################
ip_to_serve_from = '127.0.0.1'                                                       #
url_prefix = urllib.quote('')                                                        # e.g.: '/pygal'
secret_key = 'This should be a real secret string including all kinds of characters' # create this e.g. by the following command: binascii.hexlify(os.urandom(24))
token_valid_time = 60 * 60 * 1                                                       # 1 hour
admin_group = []                                                               #
######################################################################################
# Mail server configuration                                                          #
######################################################################################
sendmail_cmd = None                                                                  # e.g.: '/usr/sbin/sendmail'
from_adr = None                                                                      # e.g.: 'pygal@127.0.0.1'
######################################################################################

############################################################################################
# Parameters configuring the gallery content (delete cache after changing in this section) #
############################################################################################
show_pictures = True                                                                       #
show_videos = True                                                                         #
show_audio = False                                                                         #
show_other = False                                                                         #
inverse_sorting = False                                                                    #
############################################################################################
# Content pathes (be aware that those pathes exists)                                       #
############################################################################################
temp_path = os.path.join(basepath, 'data', 'tmp')                                          #
staging_path = os.path.join(basepath, 'data', 'staging')                                   #
item_path = os.path.join(basepath, 'data', 'items')                                        #
database_path = os.path.join(basepath, 'data', 'database')                                 #
cache_path = os.path.join(basepath, 'data', 'cache')                                       #
whoosh_path = os.path.join(basepath, 'data', 'whoosh')                                     #
############################################################################################

#########################################################
# Theme and X-Nail-Size                                 #
#########################################################
theme_path = os.path.join(basepath, 'themes', 'clereg') #
thumbnail_size_list = [137, 225, 500]                   #
thumbnail_size_default = 1                              #
webnail_size_list = [1000, 2000]                        #
webnail_size_default = 1                                #
#########################################################
