import itertools
import numpy as np
import pandas as pd
import logging
from dataclasses import dataclass, make_dataclass
from colorama import Fore, Back, Style


# tiles
TILE_EMPTY = ' '
KING = 'ﱃ'
PAWN = 'P'
QUEEN = 'Q'
ROOK = 'T'
HORSE = 'H'
BISHOP = 'B'
PIECES = [TILE_EMPTY, KING, PAWN, QUEEN, ROOK, HORSE, BISHOP]

# colors
BG_LIGHT = Back.WHITE
BG_DARK = Back.BLACK
FG_DARK = Fore.BLUE
FG_LIGHT = Fore.LIGHTMAGENTA_EX
FG_EMPTY = ''
BG_MOVE_START = Back.YELLOW
BG_MOVE_EMPTY = Back.LIGHTCYAN_EX
BG_MOVE_OPONENT = Back.RED
BOLD = '\033[1m'

P0 = 0
P1 = 1
NO_PLAYER = 2

COL_NAMES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

# offsets
#
#    7  8  9
#   -1  P  1
#   -9 -8 -7
#
OFFSETS = [8, -8, -1, 1, 7, -7, 9, -9]

def format_text(text, is_bg_light=True, is_fg_light=True, add_space=False, add_bg=True):
    spc = ' ' if add_space else ''
    text_spaced = f'{spc}{text}{spc}'
    fg = FG_LIGHT if is_fg_light else FG_DARK
    
    if add_bg:
        bg = BG_LIGHT if is_bg_light else BG_DARK
    else:
        bg = ''

    return f'{bg}{fg}{text_spaced}{Style.RESET_ALL}'

def format_text_spaced(text, bg, fg, is_bold=True):
    bold = BOLD if is_bold else ''
    return f'{bg}{fg}{bold} {text} {Style.RESET_ALL}'

def piece_to_id(piece):
    return PIECES.index(piece)

def id_to_piece(id):
    return id[1] == 0, PIECES[id[0]]

def str_to_index(coords):
    splitted = [*coords]
    if len(splitted) < 2:
        logging.warning('Too short coords')
        return None

    col = COL_NAMES.index(splitted[0]) if splitted[0] in COL_NAMES else None
    if col is None: return None

    row = None

    try:
        row = int(splitted[1])
    except ValueError:
        print('Than\'s not number!')

    row = row - 1 if row in range(1,9) else None
    return None if row is None else row * 8 + col
    
def is_valid_pos(pos):
    return pos >= 0 & pos < 8*8

def index_to_row_col(pos):
    r = pos // 8
    c = pos - r * 8
    return r, c

def index_to_loc(index):
    r, c = index_to_row_col(index)
    r += 1
    col = COL_NAMES[c]
    return r, col

class Piece:
    def __init__(self, name, is_sliding, color):
        self.name = name
        self.is_sliding = is_sliding
        self.color = color
        self.is_first_move = True
        self.player = NO_PLAYER
        if color == FG_LIGHT:
            self.player = P0
        if color == FG_DARK:
            self.player = P1
        

@dataclass
class Tile:
    piece: Piece
    color: str
    color_alt: str = ''

Move = make_dataclass("Move", [("start", int), ("target", int)])

    
class Chessboard:
    def __init__(self):
        board_np = np.full((8, 8), Tile(Piece(TILE_EMPTY, False, FG_EMPTY), BG_DARK))

        # initialize pieces
        board_np[1, :] = Tile(Piece(PAWN,   False, FG_DARK), BG_DARK)
        board_np[0, 0] = Tile(Piece(ROOK,   True,  FG_DARK), BG_DARK)
        board_np[0, 1] = Tile(Piece(HORSE,  False, FG_DARK), BG_DARK)
        board_np[0, 2] = Tile(Piece(BISHOP, True,  FG_DARK), BG_DARK)
        board_np[0, 3] = Tile(Piece(QUEEN,  True,  FG_DARK), BG_DARK)
        board_np[0, 4] = Tile(Piece(KING,   False, FG_DARK), BG_DARK)
        board_np[0, 5] = Tile(Piece(BISHOP, True,  FG_DARK), BG_DARK)
        board_np[0, 6] = Tile(Piece(HORSE,  False, FG_DARK), BG_DARK)
        board_np[0, 7] = Tile(Piece(ROOK,   True,  FG_DARK), BG_DARK)
        
        board_np[6, :] = Tile(Piece(PAWN,   False, FG_LIGHT), BG_DARK)
        board_np[7, 0] = Tile(Piece(ROOK,   True,  FG_LIGHT), BG_DARK)
        board_np[7, 1] = Tile(Piece(HORSE,  False, FG_LIGHT), BG_DARK)
        board_np[7, 2] = Tile(Piece(BISHOP, True,  FG_LIGHT), BG_DARK)
        board_np[7, 3] = Tile(Piece(KING,   False, FG_LIGHT), BG_DARK)
        board_np[7, 4] = Tile(Piece(QUEEN,  True,  FG_LIGHT), BG_DARK)
        board_np[7, 5] = Tile(Piece(BISHOP, True,  FG_LIGHT), BG_DARK)
        board_np[7, 6] = Tile(Piece(HORSE,  False, FG_LIGHT), BG_DARK)
        board_np[7, 7] = Tile(Piece(ROOK,   True,  FG_LIGHT), BG_DARK)

        for r, c in itertools.product(range(8), range(8)):
            color = BG_LIGHT if (r + c) % 2 != 0 else BG_DARK
            board_np[r, c] = Tile(board_np[r, c].piece, color)

        self.board = pd.DataFrame(board_np)
        self.board.columns = COL_NAMES
        self.board.index = reversed(range(1, 9))
        
        # precompile move data
        # indexed from bottom left
        self.squares_to_edge = np.empty((8*8, 8), dtype=int)
        
        for r, c in itertools.product(range(8), range(8)):
            up = 7 - r
            down = r
            left = c
            right = 7 - c
            
            index = r * 8 + c
            
            self.squares_to_edge[index] = [
                up,
                down,
                left,
                right,
                min(up, left),
                min(down, right),
                min(up, right),
                min(down, left)
            ]
        
    def generate_moves(self, player):
        moves = []

        # check each tile for pieces of active player
        for tile_index in range(64):
            r, c = index_to_loc(tile_index)
            piece = self.board.loc[r, c].piece
            if piece.player == player:
                if piece.is_sliding: 
                    new_moves = self.generate_sliding_moves(tile_index, piece)
                    moves = [*moves, *new_moves]
                elif piece.name == KING:
                    new_moves = self.generate_king_moves(tile_index, piece)
                    moves = [*moves, *new_moves]
                elif piece.name == PAWN:
                    new_moves = self.generate_pawn_moves(tile_index, piece)
                    moves = [*moves, *new_moves]
                elif piece.name == HORSE:
                    new_moves = self.generate_horse_moves(tile_index, piece)
                    moves = [*moves, *new_moves]

        moves_flat = np.array(moves)
        print(moves_flat)
        return moves_flat
        
    def generate_sliding_moves(self, start_index, piece):
        moves = []

        start_dir = 4 if piece.name == BISHOP else 0
        end_dir = 4 if piece.name == ROOK else 8

        # check squares to edge for each direction
        for direction in range(start_dir, end_dir):
            for distance in range(self.squares_to_edge[start_index, direction]):

                target_index = start_index + OFFSETS[direction] * (distance + 1)
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # blocked by firendly piece
                if target_piece.player == piece.player: break

                moves.append(Move(start_index, target_index))

                # don't continue if captured oponent
                if target_piece.player != NO_PLAYER: break
        return moves
    
    def generate_king_moves(self, start_index, piece):
        moves = []
        
        for direction in range(8):
            if self.squares_to_edge[start_index, direction] > 0:
                target_index = start_index + OFFSETS[direction]
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # blocked by firendly piece
                if target_piece.player == piece.player: continue

                moves.append(Move(start_index, target_index))

        return moves
    
    def generate_pawn_moves(self, start_index, piece):
        moves = []
        distance = 2 if piece.is_first_move else 1
        forward_offset = 0 if piece.player == P0 else 1
        
        # check ahead
        for dist in range(distance):
            if self.squares_to_edge[start_index, forward_offset] > dist:
                
                target_index = start_index + OFFSETS[forward_offset] * (dist + 1)
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by piece
                if target_piece.player == NO_PLAYER:
                    moves.append(Move(start_index, target_index))
                
        # check sides for oponent
        side_offsets = [7, 9] if piece.player == P0 else [-7, -9]
        for offset in side_offsets:
            if self.squares_to_edge[start_index, OFFSETS.index(offset)] > 0:
                
                target_index = start_index + offset
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # found oponent
                if (target_piece.player != piece.player) & (target_piece.player != NO_PLAYER):
                    moves.append(Move(start_index, target_index))

        return moves
    
    def generate_horse_moves(self, start_index, piece):
        moves = []
        
        count_top = self.squares_to_edge[start_index, 0]
        count_bot = self.squares_to_edge[start_index, 1]
        count_left = self.squares_to_edge[start_index, 2]
        count_right = self.squares_to_edge[start_index, 3]
        
        # check possible tiles one by one
        #
        #    2   1 
        #  4       3
        #      X
        #  5       6
        #    7   8
        #

        if count_top > 1:
            if count_right > 0:
                target_index = start_index + OFFSETS[0] * 2 + 1
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
            if count_left > 0:
                target_index = start_index + OFFSETS[0] * 2 - 1
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
        
        if count_top > 0:
            if count_right > 1:
                target_index = start_index + OFFSETS[0] + 2
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
            if count_left > 1:
                target_index = start_index + OFFSETS[0] - 2
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))

        if count_bot > 1:
            if count_right > 0:
                target_index = start_index + OFFSETS[1] * 2 + 1
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
            if count_left > 0:
                target_index = start_index + OFFSETS[1] * 2 - 1
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
        
        if count_bot > 0:
            if count_right > 1:
                target_index = start_index + OFFSETS[1] + 2
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
            if count_left > 1:
                target_index = start_index + OFFSETS[1] - 2
                target_r, target_c = index_to_loc(target_index)
                target_piece = self.board.loc[target_r, target_c].piece
                
                # not blocked by firendly piece
                if target_piece.player != piece.player:
                    moves.append(Move(start_index, target_index))
        
        return moves

def draw_board(board_pd):
    board = ''

    for i, row in board_pd.iterrows():
        line = f'{i} '
        for tile in row:
            bg = tile.color if tile.color_alt == '' else tile.color_alt
            line += format_text_spaced(tile.piece.name, bg, tile.piece.color)
        board += f'{line}\n'
    col_names = '  '.join(list(board_pd.columns))
    board += f'   {col_names}'
    print(board)


def move(board: pd.DataFrame, commands, player):
    # sourcery skip: instance-method-first-arg-name
    if len(commands) < 2:
        logging.warning('Not enough commands')
        return False
    
    c_old, r_old = [*commands[0]]
    c_new, r_new = [*commands[1]] 
    
    try:
        r_old = int(r_old)
        r_new = int(r_new)
    except ValueError:
        return False

    tile_old = board.loc[r_old, c_old]
    tile_new = board.loc[r_new, c_new]

    if r_old not in range(1, 9):    return False
    if c_old not in COL_NAMES:      return False
    if tile_old.piece.player != player: return False

    board._set_value(r_new, c_new, Tile(tile_old.piece, tile_new.color))
    board._set_value(r_old, c_old, Tile(Piece(TILE_EMPTY, False, FG_EMPTY), tile_old.color))
    
    return True

def show_moves(board: pd.DataFrame, piece_loc, moves):
    board_colored = board.copy()

    index = str_to_index(piece_loc)
    loc_r, loc_c = index_to_loc(index)
    selected_tile = board_colored.loc[loc_r, loc_c]

    board_colored.loc[loc_r, loc_c] = Tile(selected_tile.piece, selected_tile.color, BG_MOVE_START)

    for move in np.array([m for m in moves if m.start == index]):
        r, c = index_to_loc(move.target)
        target_tile = board_colored.loc[r, c]

        if target_tile.piece.player == NO_PLAYER:
            board_colored.loc[r, c] = Tile(target_tile.piece, target_tile.color, BG_MOVE_EMPTY)
            continue
        board_colored.loc[r, c] = Tile(target_tile.piece, target_tile.color, BG_MOVE_OPONENT)

    return board_colored