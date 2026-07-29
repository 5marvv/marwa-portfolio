def print_board(board):
    print("\n")
    print(f" {board[0]} | {board[1]} | {board[2]} ")
    print("-----------")
    print(f" {board[3]} | {board[4]} | {board[5]} ")
    print("-----------")
    print(f" {board[6]} | {board[7]} | {board[8]} ")
    print("\n")

def check_win(b, player):
    win_states = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Columns
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]
    return any(all(b[cell] == player for cell in state) for state in win_states)

def run_game():
    board = [str(i+1) for i in range(9)]
    current_player = "X"
    
    print("--- TIC-TAC-TOE ---")
    
    for turn in range(9):
        print_board(board)
        try:
            move = int(input(f"Player {current_player}, choose a spot (1-9) or '0' to quit: ")) - 1
            if move == -1:
                break
            if board[move] in ["X", "O"]:
                print("Spot already taken! Try again.")
                continue
            board[move] = current_player
        except (ValueError, IndexError):
            print("Invalid input. Pick a number between 1 and 9.")
            continue
            
        if check_win(board, current_player):
            print_board(board)
            print(f"Congratulations! Player {current_player} wins!")
            break
            
        current_player = "O" if current_player == "X" else "X"
    else:
        print_board(board)
        print("It's a draw!")

if __name__ == "__main__":
    run_game()