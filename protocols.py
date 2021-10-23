MESSAGE_SEPARATOR = '|'
NEWLINE = '\n'

ANDROID_HEADER = 'AND'
STM_HEADER = 'STM'
ALGORITHM_HEADER = 'ALG'


class Status:
    IDLE = 'idle'
    IMG_REC = 'img rec'
    FASTEST_PATH = 'fastest path'


class AndroidToSTM:

    MOVE_FORWARD = 'w'
    MOVE_BACK = 's'
    TURN_LEFT = 'a'
    TURN_RIGHT ='d'
    CENTER = 'c'

    ALL_MESSAGES = [
        MOVE_FORWARD,
        MOVE_BACK,
        TURN_LEFT,
        TURN_RIGHT,
        CENTER,
    ]


class AndroidToAlgorithm:
    START_IMGREC = 'BANANAS' #keyword sent to indicate start of img rec wk8
    START_FASTEST_PATH = 'LEMON' #keyword sent to indicate start of fastest path wk9
    DRAW_PATH = 'DRAW_PATH'
    RESET = "RESET"


class AlgorithmToRPi:
    TAKE_PICTURE = 'R'
    EXPLORATION_COMPLETE = 'S'
    


class RPiToAlgorithm:
    DONE_TAKING_PICTURE = 'D'
    DONE_IMG_REC = 'I'
    NOTHING_DETECTED = 'None'