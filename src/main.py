from chessboard import Chessboard, move, format_text, show_moves, draw_board, P0, P1, move_lazy
from logic import chooseComputerMove
from colorama import Fore, Back, Style
import os


if __name__ == '__main__':
    print(f'\n   {Back.BLACK}{Fore.WHITE} WELCOME TO CHESS {Style.RESET_ALL}\n')

    chessboard = Chessboard()
    is_playing = True
    active_player = P0    
    edited_board = chessboard.board.copy()
    draw_edited_board = False

    while is_playing:
        os.system('clear')
        if draw_edited_board:
            draw_board(edited_board)
            draw_edited_board = False
        else:
            draw_board(chessboard.board)

        moves = chessboard.generate_legal_moves(active_player)
        
        # make move by computer if active
        if active_player == P1:
            selected_move = chooseComputerMove(moves)[0]
            move_lazy(chessboard.board, selected_move.start, selected_move.target)
            active_player = P0
            continue

        input_prefix = format_text(f'> Player {active_player}: ', is_fg_light=active_player == 0, add_bg=False)
        text = input(input_prefix)

        # translate commands
        splitted = text.split()
        if len(splitted) == 0:
            active_player = 1 if active_player == 0 else 0 
        
        elif splitted[0] == 'exit':
            is_playing = False

        elif splitted[0] == 'move':

            if is_valid_move := move(chessboard.board, splitted[1:], active_player, moves):
                active_player = 1 if active_player == 0 else 0 
        
        elif splitted[0] == 'show':
            edited_board = show_moves(chessboard.board, splitted[1], moves)
            draw_edited_board = True