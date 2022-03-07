from translate import Translator as tr

class Translator:
    def __init__(self, config):
        self.invalid_provider = False
        provider = config['default']['provider']
        to_lang = config['default']['to_lang']

        if provider == 'deepl':
            secret_access_key = config['deepl']['secret_access_key']
            pro = config['deepl'].getboolean('pro')
            self.translator_instance = tr(provider=provider, to_lang=to_lang, secret_access_key=secret_access_key, pro=pro)
        elif provider == 'microsoft':
            secret_access_key = config['microsoft']['secret_access_key']
            self.translator_instance = tr(provider=provider, to_lang=to_lang, secret_access_key=secret_access_key)
        elif provider == 'mymemory':
            email = self.config['mymemory']['email']
            self.translator_instance = tr(provider=provider, to_lang=to_lang, email=email)
        elif provider == 'libre':
            secret_access_key = config['libre']['secret_access_key']
            base_url = config['libre']['base_url']
            self.translator_instance = tr(provider=provider, to_lang=to_lang, secret_access_key=secret_access_key, base_url=base_url)
        else:
           self.invalid_provider = True


    def translate(self, message):
        if self.invalid_provider:
            return "Invalid provider specified in config!"
        try:
            return self.translator_instance.translate(message)
        except:
            return "Error! Check your config for wrong secret key/email etc!"
        
        