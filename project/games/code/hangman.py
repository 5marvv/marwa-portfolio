import random

words = ["python", "developer", "aesthetic", "minimal", "logic", "creative"]

def run_hangman():
    word = random.choice(words)
    guessed = set()
    attempts = 6
    
    print("\n--- MINIMAL HANGMAN ---")
    
    while attempts > 0:
        # Display the secret word structure (e.g., d _ v _ l o p _ r)
        display_word = [char if char in guessed else "_" for char in word]
        print("\nWord: " + " ".join(display_word))
        print(f"Attempts remaining: {attempts}")
        
        if "_" not in display_word:
            print("★ Genius! You guessed the word. ★")
            break
            
        guess = input("Guess a letter (or 'Q' to quit): ").lower()
        if guess == 'q':
            break
            
        if len(guess) != 1 or not guess.isalpha():
            print("Please enter a single valid letter.")
            continue
            
        if guess in guessed:
            print("You already guessed that letter!")
            continue
            
        guessed.add(guess)
        
        if guess not in word:
            attempts -= 1
            print("Not in the word. Try again.")
            
    else:
        print(f"\nGame over. The word was: {word}")

if __name__ == "__main__":
    run_hangman()