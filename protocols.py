MESSAGE_SEPARATOR = '|'
NEWLINE = '\n'

ANDROID_HEADER = 'AND'
STM_HEADER = 'STM'
ALGORITHM_HEADER = 'ALG'


class Status:
    IDLE = 'idle'
    EXPLORING = 'exploring'
    FASTEST_PATH = 'fastest path'


class AndroidToSTM:
    #MOVE_FORWARD = 'W1|'
    #MOVE_BACK = 'S1|'
    #TURN_LEFT = 'A|'
    #TURN_RIGHT = 'D|'
    #DO_SHORTCUT_1 = 'F1|'
    #DO_SHORTCUT_2 = 'F2|'

    MOVE_FORWARD = 'w'
    MOVE_BACK = 's'
    TURN_LEFT = 'a'
    TURN_RIGHT ='d'
    CENTER = 'c'
    DO_SHORTCUT_1 = 'F1|'
    DO_SHORTCUT_2 = 'F2|'

    ALL_MESSAGES = [
        MOVE_FORWARD,
        MOVE_BACK,
        TURN_LEFT,
        TURN_RIGHT,
        CENTER,
        DO_SHORTCUT_1,
        DO_SHORTCUT_2,
    ]


class AndroidToAlgorithm:
    START_IMGREC = 'BANANAS'
    START_FASTEST_PATH = 'LEMON'
    SEND_ARENA = 'SendArena'
    DRAW_PATH = 'DRAW_PATH'
    RESET = "RESET"



class AndroidToRPi:
    CALIBRATE_SENSOR = 'SS|'


class AlgorithmToAndroid:
    MOVE_FORWARD = 'W'[0]
    TURN_LEFT = 'A'[0]
    TURN_RIGHT = 'D'[0]
    CALIBRATING_CORNER = 'L'[0]
    SENSE_ALL = 'Z'[0]
    ALIGN_RIGHT = 'B'[0]
    ALIGN_FRONT = 'V'[0]

    MDF_STRING = 'M'[0]


class AlgorithmToRPi:
    TAKE_PICTURE = 'R'
    EXPLORATION_COMPLETE = 'S'
    


class RPiToAndroid:
    STATUS_EXPLORING = '{"status":"exploring"}'
    STATUS_FASTEST_PATH = '{"status":"fastest path"}'
    STATUS_TURNING_LEFT = '{"status":"turning left"}'
    STATUS_TURNING_RIGHT = '{"status":"turning right"}'
    STATUS_IDLE = '{"status":"idle"}'
    STATUS_TAKING_PICTURE = '{"status":"taking picture"}'
    STATUS_CALIBRATING_CORNER = '{"status":"calibrating corner"}'
    STATUS_SENSE_ALL = '{"status":"sense all"}'
    STATUS_MOVING_FORWARD = '{"status":"moving forward"}'
    STATUS_ALIGN_RIGHT = '{"status":"align right"}'
    STATUS_ALIGN_FRONT = '{"status":"align front"}'
    
    MOVE_UP = '{"move":[{"direction":"forward"}]}'
    TURN_LEFT = '{"move":[{"direction":"left"}]}'
    TURN_RIGHT = '{"move":[{"direction":"right"}]}'


class RPiToSTM:
    CALIBRATE_SENSOR = 'L|A|'
    START_EXPLORATION = 'E|'
    START_FASTEST_PATH = 'F|'


class RPiToAlgorithm:
    DONE_TAKING_PICTURE = 'D'
    DONE_IMG_REC = 'I'
    NOTHING_DETECTED = 'None'