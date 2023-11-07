import watchdog.events
import watchdog.observers
import time
import copy


watch_path = "."

class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self, zip_name):
        self.zip_name = zip_name
        self.filename = None
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.zip'], ignore_directories=True, case_sensitive=False)
    
    def on_any_event(self, event):
        print(f'evento detectado {event.event_type}')
        if(event.event_type == 'modified'):
            self.filename = event.src_path.split('/')[-1]
            print(f'modificacion: {self.filename}')
            

        return event.src_path


__timeout = 30
def downloaded_file(zip_wanted):
    print(f'zip wanted {zip_wanted}')

    event_handler = Handler(zip_wanted)
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=watch_path, recursive=True)
    observer.start()

    trys = 0
    try:
        print(f'se inicio con {event_handler.filename}')
        while(event_handler.filename is None):
            time.sleep(1)

            if __timeout == trys:
                raise Exception("se canso de esperar")

            trys += 1
            print(f'esperando {trys}')
        
    except Exception as ex:
        observer.stop()
        raise(Exception(ex))

    observer.stop()
    observer.join() 
    return event_handler.filename