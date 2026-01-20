uint16 left_motor_ctrl_word
int32 left_motor_speed
int32 left_motor_encoder
uint16 left_motor_status
uint8 left_motor_error
uint32 left_motor_error_hist1
uint32 left_motor_error_hist2
int32 left_motor_current
uint16 left_motor_i2t_motor
uint16 left_motor_i2t_controller
int16 left_motor_temperature
uint16 right_motor_ctrl_word
int32 right_motor_speed
int32 right_motor_encoder
uint16 right_motor_status
uint8 right_motor_error
uint32 right_motor_error_hist1
uint32 right_motor_error_hist2
int32 right_motor_current
uint16 right_motor_i2t_motor
uint16 right_motor_i2t_controller
int16 right_motor_temperature
#Status bits for brake feedback.
uint8 BRAKE_STATUS_BRAKED_BIT=1		# is "1" if brake is supposed to be braked
uint8 BRAKE_STATUS_FB_BIT=4			# is "1" if brake feedback sensor is activated (brake is released)
uint8 BRAKE_STATUS_TRANSITION_BIT=128
# So error combinations are - (Any combination with the TRANSITION bit set are valid)
#  BRAKED	FB	TRANSITION	STATUSWORD
#	0		0	0			0x00			Brake is suppused to be released, but FB indicate braked. We are not in transition.
#	1		1	0			0x05			Brake is suppused to be braked, but FB indicate released. We are not in transition.
uint8 brake_left_status
uint8 brake_right_status
