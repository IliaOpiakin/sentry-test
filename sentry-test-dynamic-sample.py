import sentry_sdk
from sentry_sdk.types import Event, Hint
import time
from datetime import datetime
import random

# white space

captured_exceptions = set()

def custom_error_sampler(event: Event, hint: Hint) -> float:
    global captured_exceptions
    error_class = hint["exc_info"][0]
    if error_class not in captured_exceptions:
        captured_exceptions.add(error_class)
        return 1.0  # Always capture the first appearance of this error type
    return 0.01  # Default sample rate for other errors

def traces_sampler(sampling_context):
    # Always capture the first error
    if sampling_context['parent_sampled'] is None:
        return 1.0
    # Default sample rate for other errors
    return 0.01

def my_error_sampler(event: Event, hint: Hint) -> float:
    error_class = hint["exc_info"][0]

    if error_class == ValueError:
        return 0.01
    elif error_class == ModuleNotFoundError:
        return 0.1
    elif error_class == KeyError:
        return 1.0

    # All the other errors
    return 1.0

# Initialize captured exceptions dictionary and timestamp
captured_exceptions = {}
first_error_timestamp = None
info_message_timestamp = None

def custom_error_sampler_v2(event: Event, hint: Hint) -> float:
    global captured_exceptions
    global first_error_timestamp
    global info_message_timestamp
    error_class = hint["exc_info"][0].__name__
    
    if info_message_timestamp is None:
        info_message_timestamp = time.time()
    

    time_since_the_last_info = time.time() - info_message_timestamp
    # Send to Sentry short sumamry every 5 minutes
    if time_since_the_last_info > 60:
        info_message_timestamp = time.time()
        message = "Info: Captured exceptions" 
        for error_class, details in captured_exceptions.items():
            sentry_sdk.set_extra(error_class, details['count'])
        sentry_sdk.capture_message(message, level="info")
        
    # Check if the error class has been captured before
    if error_class not in captured_exceptions:
        captured_exceptions[error_class] = {
            "count": 1,
            "timestamp": time.time()
        }
        return 1.0  # Always capture the first appearance of this error type
    else:
        captured_exceptions[error_class]["count"] += 1

    # Calculate the time elapsed since the first error of this type
    elapsed_time = time.time() - captured_exceptions[error_class]["timestamp"]

    # Adjust the sample rate to capture at least one error per minute for each error type
    if elapsed_time > 60:
        captured_exceptions[error_class]["timestamp"] = time.time()
        return 1.0
    else:
        return 0.01  # Default sample rate for other errors

     

sentry_sdk.init(
    dsn="https://2d602fd2c90a2e6543e586d96c8ec3a1@sentry.vault6.tech/3",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    #sample_rate=0.01,
    error_sampler=custom_error_sampler_v2, 
    #traces_sampler=traces_sampler,
)

# Initialize statistics dictionary
statistic = {
    "ZeroDivisionError": 0,
    "IndexError": 0,
    "KeyError": 0,
    "ModuleNotFoundError": 0,
    "ValueError": 0
}

# Function to simulate errors
def simulate_errors():
    sleep_time = 0.02
    for _ in range(1000000):
        a = random.randint(1, 10000)

        try:
            if a == 1:
                if statistic["ZeroDivisionError"] == 0:
                    print("Hey ho - we got ZeroDivisionError exception!!   [Unique]")
                    result = 10 / 0
                else:
                    continue

            elif 1 < a <= 10:
                print("Hey ho - we got IndexError exception!!   [Rare]")
                my_list = [1, 2, 3]
                print(my_list[5])

            elif 10 < a <= 100:
                my_dict = {"key": "value"}
                print(my_dict["nonexistent_key"])

            elif 100 < a <= 1000:
                import non_existent_module

            elif a > 1000:
                int("not_a_number")

        except ZeroDivisionError as e:
            statistic["ZeroDivisionError"] += 1
            sentry_sdk.capture_exception(e)

        except IndexError as e:
            statistic["IndexError"] += 1
            sentry_sdk.capture_exception(e)

        except KeyError as e:
            statistic["KeyError"] += 1
            sentry_sdk.capture_exception(e)

        except ImportError as e:
            statistic["ModuleNotFoundError"] += 1
            sentry_sdk.capture_exception(e)

        except ValueError as e:
            statistic["ValueError"] += 1
            sentry_sdk.capture_exception(e)

        time.sleep(sleep_time)

# Run the simulation
simulate_errors()

# Print statistics
for error_type, count in statistic.items():
    print(f"{error_type}: {count}")

print("Total:", sum(statistic.values()))
print(statistic)



# 23:39 First run 100.000 issues, delay 0.01 seconds CPU 100%
# CPU 100%
# ZeroDivisionError         1
# IndexError               88
# KeyError                885
# ModuleNotFoundError    8879
# ValueError            90137
# ---------------------------
# Total:                99990

# 08:14 Second run 100.000 issues, delay 0.01 seconds
# CPU 100%
# ZeroDivisionError         1
# IndexError               88
# KeyError                958
# ModuleNotFoundError    9081
# ValueError            89865
# ---------------------------
# Total:                99993

# 09:10 First run 100.000 issues, sample 0.01 (1%), delay 0.01 seconds
# CPU 8%
# ZeroDivisionError         1  -> 1% =   0.01  (Captured =    0)
# IndexError               64  -> 1% =   0.64  (Captured =    1)
# KeyError                901  -> 1% =   9.01  (Captured =   14)
# ModuleNotFoundError    8829  -> 1% =  88.29  (Captured =   87)
# ValueError            90199  -> 1% = 901.99  (Captured =  846)
# --------------------------------------------------------------
# Total:                99994  -> 1% = 999.94  (Captured =  948)


# 09:41 Second run 100.000 issues, sample 0.01 (1%), delay 0.01 seconds
# CPU 8%
# ZeroDivisionError         1  -> 1% =   0.01  (Captured =    0)
# IndexError               81  -> 1% =   0.81  (Captured =    1)
# KeyError                916  -> 1% =   9.16  (Captured =    7)
# ModuleNotFoundError    8968  -> 1% =  89.68  (Captured =   83)
# ValueError            90030  -> 1% = 900.30  (Captured =  937)
# --------------------------------------------------------------
# Total:                99996  -> 1% = 999.96  (Captured = 1028)


# 10:25 First run 100.000 issues, custom_error_sampler with default sample 0.01 (1%), delay 0.01 seconds
# CPU 7%
# ZeroDivisionError         1  -> 1% =   0.01  (Captured =    1)
# IndexError               90  -> 1% =   0.90  (Captured =    3)
# KeyError                872  -> 1% =   8.72  (Captured =    6)
# ModuleNotFoundError    8939  -> 1% =  89.39  (Captured =   93)
# ValueError            90086  -> 1% = 900.86  (Captured =  886)
# --------------------------------------------------------------
# Total:                99988  -> 1% = 999.88  (Captured =  989)


# 12:58 Second run 100.000 issues, custom_error_sampler with default sample 0.01 (1%), delay 0.01 seconds
# CPU 7%
# ZeroDivisionError         1  -> 1% =   0.01  (Captured =    1)
# IndexError              102  -> 1% =   1.02  (Captured =    2)
# KeyError                880  -> 1% =   8.80  (Captured =   12)
# ModuleNotFoundError    9047  -> 1% =  90.47  (Captured =   98)
# ValueError            89957  -> 1% = 899.57  (Captured =  940)
# --------------------------------------------------------------
# Total:                99987  -> 1% = 999.87  (Captured = 1053)
