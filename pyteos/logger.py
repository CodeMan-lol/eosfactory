import enum
import inspect
from termcolor import cprint, colored
import setup

def translate(msg):
    import eosf
    return eosf.accout_names_2_object_names(setup.heredoc(msg))

class AccountNotExist:
    msg_template = '''
Account ``{}`` does not exist in the blockchain. It may be created.
'''
    def __init__(self, msg):
        self.msg = translate(msg)

class WalletExists:
    msg_template = '''
Account ``{}`` does not exist in the blockchain. It may be created.
'''
    def __init__(self, msg):
        self.msg = translate(msg)

class WalletNotExist:
    msg_template = '''
Wallet ``{}`` does not exist.
'''
    def __init__(self, msg):
        self.msg = translate(msg)

class InvalidPassword:
    msg_template = '''
Invalid password for wallet {}.
'''
    def __init__(self, msg):
        self.msg = translate(msg)

class LowRam:
    msg_template = '''
Ram needed is {}kB, deficiency is {}kB.
'''
    def __init__(self, needs, deficiency):
        self.needs = needs
        self.deficiency = deficiency
        self.msg = translate(msg_template.format(needs, deficiency))    

class Error:
    def __init__(self, msg):
        self.msg = translate(msg)


class Verbosity(enum.Enum):
    COMMENT = ['green', None, []]
    INFO = ['blue', None, ['bold']]
    TRACE = ['blue', None, []]
    ERROR = ['red', None, []]
    ERROR_TESTING = ['magenta', None, []]
    OUT = ['']
    OUT_INFO = ['magenta', 'on_green', []]
    DEBUG = ['yellow', None, []]

_is_throw_error = False
def set_throw_error(status=False):
    global _is_throw_error
    _is_throw_error = status

_is_testing_error = False
def set_is_testing_errors(status=True):
    '''Changes the color of the ``ERROR`` logger printout.

    Makes it less alarming.
    '''
    global _is_testing_error
    _is_testing_error = status

class Logger():
    verbosity = [Verbosity.TRACE, Verbosity.OUT, Verbosity.DEBUG]

    def __init__(self, verbosity=None):
        if verbosity is None:
            self._verbosity = Logger.verbosity
        else:
            self._verbosity = verbosity

        self.cleos_object = None
        self.eosf_buffer = ""
        self.out_buffer = ""
        self.out_info_buffer = ""
        self.error_buffer = ""
        self.debug_buffer = ""

    def COMMENT(self, msg):
        frame = inspect.stack()[1][0]
        test_name = inspect.getframeinfo(frame).function
        color = Verbosity.COMMENT.value
        cprint(
            "\n###  " + test_name + ":\n" + translate(msg) + "\n",
            color[0], color[1], attrs=color[2])

    def SCENARIO(self, msg):
        self.COMMENT(msg)

    def TRACE(self, msg, do=False):
        msg = translate(msg)
        self.eosf_buffer = msg
        if msg and (Verbosity.TRACE in self._verbosity or do):
            color = Verbosity.TRACE.value
            cprint(msg, color[0], color[1], attrs=color[2])

    def INFO(self, msg, do=False):
        if msg and (Verbosity.INFO in self._verbosity or do):
            color = Verbosity.INFO.value
            cprint(translate(msg), color[0], color[1], attrs=color[2])

    def TRACE_INFO(self, msg, do=False):
        if msg and Verbosity.TRACE in self._verbosity:
            self.TRACE(msg, do)
        else:
            self.INFO(msg, do)

    def OUT_INFO(self, msg, do=False):
        msg = translate(msg)
        self.out_info_buffer = msg

        error = False
        try:
            error = msg.error
        except:
            pass

        try:
            msg = err_msg.err_msg
        except:
            pass

        if msg and (Verbosity.OUT_INFO in self._verbosity or do):
            color = Verbosity.OUT_INFO.value
            cprint(msg, color[0], color[1], attrs=color[2])            

    def OUT(self, msg, do=False):
        msg = translate(msg)
        self.out_buffer = msg

        if msg and (Verbosity.OUT in self._verbosity or do):
            print(msg + "\n")

        self.OUT_INFO(msg, do)

    def DEBUG(self, msg, do=False):
        msg = translate(msg)
        self.debug_buffer = msg

        if msg and (Verbosity.DEBUG in self._verbosity or do):
            color = Verbosity.DEBUG.value
            cprint(msg, color[0], color[1], attrs=color[2])

    def error_map(self, err_msg):
        if "main.cpp:3008" in err_msg:
            return AccountNotExist(
                AccountNotExist.msg_template.format(self.name))

        if "Error 3080001: Account using more than allotted RAM" in err_msg:
            needs = int(re.search('needs\s(.*)\sbytes\shas', err_msg).group(1))
            has = int(re.search('bytes\shas\s(.*)\sbytes', err_msg).group(1))
            return LowRam(needs//1024, (needs - has) // 1024)

        if "transaction executed locally, but may not be" in err_msg:
            return None

        if "Wallet already exists" in err_msg:
            return logger.WalletExists(
                logger.WalletExists.msg_template.format(self.name))

        if "Error 3120002: Nonexistent wallet" in err_msg:
            return logger.WalletNotExist(
                logger.WalletNotExist.msg_template.format(self.name))
 
        if "Invalid wallet password" in err_msg:
            return logger.InvalidPassword(
                logger.InvalidPassword.msg_template.format(self.name))
        
        #######################################################################
        # NOT ERRORS
        #######################################################################
        
        if "Error 3120008: Key already exists" in err_msg:
            return None                

        if not err_msg:
            return None
        return Error(err_msg)

    def switch(self, cleos_object_or_str):
        try:
            cleos_object_or_str.error_object = \
                self.error_map(cleos_object_or_str.err_msg)
        except:
            pass

        return cleos_object_or_str   
                     
    def ERROR_OBJECT(self, err_msg):
        try:
            cleos_object = self.switch(err_msg)
            return cleos_object.error_object
        except:
            return None

    def ERROR(self, cleos_or_str=None):
        '''Print an error message or throw 'Exception'.

            The 'cleos_or_str' argument may be a string error message or any object having
            the string attribute `err_msg`.

            If 'set_throw_error(True)', an `Exception object is thrown, otherwise the
            message is printed.

            arguments:
            cleos_or_str -- error message string or object having the attribute err_msg
        '''
        if cleos_or_str is None:
            cleos_or_str = self

        cleos_object = None
        if not isinstance(cleos_or_str, str):
            if not cleos_or_str.error:
                return False
                            
            cleos_object = self.switch(cleos_or_str)
            if cleos_object.error_object is None:
                return False

            msg = cleos_object.err_msg
        else:
            msg = cleos_or_str

        if not msg:
            return False

        if _is_testing_error:
            color = Verbosity.ERROR_TESTING.value
        else:
            color = Verbosity.ERROR.value

        msg = colored(
            "ERROR:\n{}".format(translate(msg)), 
            color[0], color[1], attrs=color[2])  + "\n"
        if not cleos_object is None:
            cleos_object.error_object.msg = msg

        self.error_buffer = msg
        global _is_throw_error
        if _is_throw_error:
            raise Exception(msg)
        else:
            print(msg)

        return True