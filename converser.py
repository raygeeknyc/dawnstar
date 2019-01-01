import multiprocessing
import logging
from multiprocessingloghandler import ChildMultiProcessingLogHandler, ParentMultiProcessingLogHandler

import argparse
import json
import os.path
import pathlib2 as pathlib
import argparse
import base64

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

import google.oauth2.credentials

from google.assistant.library import Assistant
from google.assistant.library.event import EventType
from google.assistant.library.file_helpers import existing_file
from google.assistant.library.device_helpers import register_device

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError


WARNING_NOT_REGISTERED = """
    This device is not registered. This means you will not be able to use
    Device Actions or see your device in Assistant Settings. In order to
    register this device follow instructions at:
    https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device
"""
class Converser(multiprocessing.Process):
    def __init__(self, event, log_queue, logging_level):
        multiprocessing.Process.__init__(self)
        self._exit = event
        self._log_queue = log_queue
        self._logging_level = logging_level
        self._init_assistant()

    def _init_logging(self):
        handler = ChildMultiProcessingLogHandler(self._log_queue)
        logging.getLogger(str(os.getpid())).addHandler(handler)
        logging.getLogger(str(os.getpid())).setLevel(self._logging_level)

    def _cleanup(self):
        logging.debug("Cleaning up")

    def run(self):
        self._init_logging()
        logging.debug("Assistant running")
        try:
            self._converse()
        except Exception, e:
            logging.exception("Error in analyzer main thread")
        finally:
            self._cleanup()
            logging.debug("Exiting image analyzer")

    def _converse(self):
        while not self._exit.is_set():
            for event in self._events:
                process_event(self._event, self._assistant)

    def take_photo(self):
        with picamera.PiCamera() as camera:
            camera.capture('image.jpg')
        
    def use_computer_vision(self, label_picture=True):
        #take picture
        take_photo()
        
        #get Google Credentials
        credentials = GoogleCredentials.get_application_default()
        service = discovery.build('vision', 'v1', credentials=credentials)
        
        if label_picture:
            with open('image.jpg','rb') as image:
                image_content = base64.b64encode(image.read())
                service_request = service.images().annotate(body={
                    'requests':[{
                        'image':{
                                'content': image_content.decode('UTF-8')
                            },
                        'features':[{
                                'type': 'LABEL_DETECTION',
                                'maxResults': 100,
                            }]
                        }]
                    })
    
                response = service_request.execute()
                print(json.dumps(response, indent=4, sort_keys=True))
    
                response_list = []
                for i in range(3):
                    clean_classification = response['responses'][0]['labelAnnotations'][i]['description']
                    response_list.append(clean_classification)
    
    
                return response_list
        else:
            with open('image.jpg','rb') as image:
                image_content = base64.b64encode(image.read())
                service_request = service.images().annotate(body={
                    'requests':[{
                        'image':{
                                'content': image_content.decode('UTF-8')
                            },
                        'features':[{
                                'type': 'FACE_DETECTION',
                            }]
                        }]
                    })
    
                response = service_request.execute()
                print(json.dumps(response, indent=4, sort_keys=True))
                response_list = response['responses'][0]['faceAnnotations'][0]
                emotion_dict = {}
                emotion_dict['surprised'] = response_list['surpriseLikelihood']
                emotion_dict['angry'] = response_list['angerLikelihood']
                emotion_dict['sad'] = response_list['sorrowLikelihood']
                emotion_dict['happy'] = response_list['joyLikelihood']
                
                l = []
                
                for key,value in emotion_dict.items():
                    if(value == "VERY_LIKELY"):
                        l.append((key,5))
                    elif(value == "LIKELY"):
                        l.append((key,4))
                    elif(value == "POSSIBLE"):
                        l.append((key,3))
                    elif(value == "UNLIKELY"):
                        l.append((key,2))
                    else:
                        l.append((key,1))
                        
                l.sort(key=lambda tup:tup[1], reverse=True)
                print("WORKING")
                emotion = l[0][0]
                print(emotion)
                return emotion
                
                    
    
    ##def sort_emotions(lst):
    ##    dict_emotions = {'VERY_UNLIKELY': 0, 'UNLIKELY': 1, 'POSSIBLE': 2, 'LIKELY': 3, 'VERY_LIKELY': 4}
    ##    for emotion in lst:
            
        
    
    def say(send, assistant, text):
        assistant.send_text_query('Repeat after me {}'.format(text))
    
    
    def handle_what_is_this(self, assistant):
        say(assistant, "hmm, let me take a look")
        verbal_list = use_computer_vision()
        if "face" in verbal_list:
            emotion = use_computer_vision(False)
            say(assistant, "I see "+verbal_list[0] + ", or " + verbal_list[1] + ", or " + verbal_list[2] + ", " + "and the face looks " + " " + emotion)
        else:
            say(assistant, "I see "+verbal_list[0] + ", or " + verbal_list[1] + ", or " + verbal_list[2])
    
    
    def handle_ship_it(self, assistant):
        say(assistant, 'Stop trying to be Sarah Cooper')
    
    def handle_what_do_you_think(self, assistant):
        say(assistant, 'Ship it')
    
    def handle_meet_your_maker(self, assistant):
        say(assistant,
           'I was created at the Google New York IOT Intern Hackathon by'
           'Stephen, Charlotte, David, Nishir, and Two')
    
    
    TRIGGERS = {
        'what is this': handle_what_is_this,
        'what is that': handle_what_is_this,
        'ship it': handle_ship_it,
        'what do you think': handle_what_do_you_think,
        'meet your maker': handle_meet_your_maker,
    }
    
    def _process_event(self, event, assistant):
        """Pretty prints events.
        Prints all events that occur with two spaces between each new
        conversation and a single space between turns of a conversation.
        Args:
            event(event.Event): The current event to process.
        """
        if event.type == EventType.ON_CONVERSATION_TURN_STARTED:
            print()
    
        print(event)
    
        if (event.type == EventType.ON_CONVERSATION_TURN_FINISHED and
                event.args and not event.args['with_follow_on_turn']):
            print()
        if event.type == EventType.ON_DEVICE_ACTION:
            for command, params in event.actions:
                print('Do command', command, 'with params', str(params))
    
        if (event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and
                event.args and 'text' in event.args):
            text = event.args['text']
            for trigger, handler in TRIGGERS.items():
                if trigger in text:
                    assistant.stop_conversation()
                    handler(assistant)
                    break
    
    def _init_assistant(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument('--device-model-id', '--device_model_id', type=str,
                            metavar='DEVICE_MODEL_ID', required=False,
                            help='the device model ID registered with Google')
        parser.add_argument('--project-id', '--project_id', type=str,
                            metavar='PROJECT_ID', required=False,
                            help='the project ID used to register this device')
        parser.add_argument('--device-config', type=str,
                            metavar='DEVICE_CONFIG_FILE',
                            default=os.path.join(
                                os.path.expanduser('~/.config'),
                                'googlesamples-assistant',
                                'device_config_library.json'
                            ),
                            help='path to store and read device configuration')
        parser.add_argument('--credentials', type=existing_file,
                            metavar='OAUTH2_CREDENTIALS_FILE',
                            default=os.path.join(
                                os.path.expanduser('~/.config'),
                                'google-oauthlib-tool',
                                'credentials.json'
                            ),
                            help='path to store and read OAuth2 credentials')
        parser.add_argument('-v', '--version', action='version',
                            version='%(prog)s ' + Assistant.__version_str__())
    
        args = parser.parse_args()
        with open(args.credentials, 'r') as f:
            credentials = google.oauth2.credentials.Credentials(token=None,
                                                                **json.load(f))
    
        device_model_id = None
        last_device_id = None
        try:
            with open(args.device_config) as f:
                device_config = json.load(f)
                device_model_id = device_config['model_id']
                last_device_id = device_config.get('last_device_id', None)
        except FileNotFoundError:
            pass
    
        if not args.device_model_id and not device_model_id:
            raise Exception('Missing --device-model-id option')
    
        # Re-register if "device_model_id" is given by the user and it differs
        # from what we previously registered with.
        should_register = (
            args.device_model_id and args.device_model_id != device_model_id)
    
        self._device_model_id = args.device_model_id or device_model_id
    
        self._assistant = Assistant(credentials, self._device_model_id)
        self._events = self._assistant.start()
    
        self._device_id = self._assistant.device_id
        logging.info('device_model_id: {}'.format(self._device_model_id))
        logging.info('device_id: {}'.format(self._device_id))
    
        # Re-register if "device_id" is different from the last "device_id":
        if should_register or (self._device_id != last_device_id):
            if args.project_id:
                self.register_device(args.project_id, credentials,
                    self._device_model_id, self._device_id)
                pathlib.Path(os.path.dirname(args.device_config)).mkdir(
                    exist_ok=True)
                with open(args.device_config, 'w') as f:
                    json.dump({
                            'last_device_id': self._device_id,
                            'model_id': self._device_model_id,
                        }, f)
            else:
                logging.warning(WARNING_NOT_REGISTERED)
        self._assistant.send_text_query("Repeat after me" + " I am a robot!")
