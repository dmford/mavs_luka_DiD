import random
import os
import math

# clearing the terminal 
os.system('cls' if os.name == 'nt' else 'clear')

# drawing a random number, hoping for even 
print("Let's try to pull an even number.")

# first attempt + result
number = random.randint(1, 100)

print(f"Number generated: {number}")

if number % 2 == 0:
    print("Result: The number was even!")
else:
    print("Result: The number was odd!")

    print("\n")

    print("Let's pull again with advantage, hoping again for an even number.")

    number1 = random.randint(1,100)
    number2 = random.randint(1,100)

    print(f"First draw: {number1}, \nSecond draw: {number2}")

    if number1 % 2 == 0 or number2 % 2 == 0: 
        print("Pulling with advantage yielded an even number!")
    else: 
        print("Pulling with advantage failed, surprisingly (P=12.5%).")
        print("\n")
        print("That seems unlikely... let's test the validity of the random number generator by pulling 1000 times.")

        successes = 0
        iterations = 1000

        for i in range(iterations): 
            number = random.randint(1,100)
            if number % 2 != 0:
                number1 = random.randint(1,100)
                number2 = random.randint(1,100)
                if number1 % 2 != 0 and number2 % 2 != 0:
                    successes += 1

        proportion = successes / (iterations)
        print(f"Proportion of even numbers drawn: {proportion:.2f}, expected around 0.125.")

        # how close is close enough? a hypothesis test
        expected_p = 0.125
        observed_p = proportion
        n = iterations + 1

        # se under H0
        se = math.sqrt(expected_p * (1-expected_p) / n)

        # z-score
        z = (observed_p - expected_p) / se

        print("\n Hypothesis Test:")
        print(f"Expected proportion (H0): {expected_p:.3f}")
        print(f"Observed proportion: {observed_p:.3f}")
        print(f"Z-score: {z:.2f}")

        # decision rule (95% CI, two-tailed)
        if abs(z) > 1.96:
            print("Result: Reject the null hypothesis, the RNG may be biased.")
        else:
            print("Result: Fail to reject the null hypothesis, the RNG appears unbiased.")
