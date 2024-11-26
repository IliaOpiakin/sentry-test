import sentry_sdk
from sentry_sdk.types import Event, Hint
import time
import random


def my_error_sampler(event: Event, hint: Hint) -> float:
    error_class = hint["exc_info"][0]

    if error_class == ValueError:
        return 0.01
    elif error_class == ModuleNotFoundError:
        return 0.05
    elif error_class == KeyError:
        return 0.1
    elif error_class == IndexError:
        return 1.0
    elif error_class == ZeroDivisionError:
        return 1.0

    # All the other errors
    return 1.0


sentry_sdk.init(
    dsn="https://8794012e3554ebd69cd11b9041c40247@sentry.vault6.tech/2",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    #sample_rate=0.1,
    error_sampler=my_error_sampler, 
)




sentry_sdk.flush(timeout=60)

statistic = {
    "ZeroDivisionError": 0,
    "IndexError": 0,
    "KeyError": 0,
    "ModuleNotFoundError": 0,
    "ValueError": 0
}

x=1
while(x<100000):
    
    a = random.randint(1, 10000)
    try:
        # Code that might raise different exceptions
        if a == 1 and statistic["ZeroDivisionError"] == 0:
            result = 10 / 0
        
        elif a >1 and a <= 10:
            my_list = [1, 2, 3]
            print(my_list[5])
        
        elif a >10 and a <= 100:
            my_dict = {"key": "value"}
            print(my_dict["nonexistent_key"])
        
        elif a >100 and a <= 1000:
            import non_existent_module
        
        elif a >1000:
            int("not_a_number")
        
    except ZeroDivisionError as e:
        #print(f"ZeroDivisionError occurred: {e}")
        statistic["ZeroDivisionError"]+=1
        sentry_sdk.capture_exception(e)

        
    except IndexError as e:
        #print(f"IndexError occurred: {e}")
        statistic["IndexError"]+=1
        sentry_sdk.capture_exception(e)
        
    except KeyError as e:
        #print(f"KeyError occurred: {e}")
        statistic["KeyError"]+=1
        sentry_sdk.capture_exception(e)
        
    except ImportError as e:
        #print(f"ModuleNotFoundError occurred: {e}")
        statistic["ModuleNotFoundError"]+=1
        sentry_sdk.capture_exception(e)
        
    except ValueError as e:
        #print(f"ValueError occurred: {e}")
        statistic["ValueError"]+=1
        sentry_sdk.capture_exception(e)

    #from sentry_sdk import capture_message
    #capture_message("Hello Sentry!")
    
    x=x+1
    time.sleep(0.01)
print(statistic)
print(sum(statistic.values()))


