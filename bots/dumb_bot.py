#  Edit the following in you favorite text editor, then paste back

#  Adjust with new vars.
translation_tick = 0
translation_tick_slice = 100
orientation_tick = 0
orientation_tick_slice = 50

tick_slice = 1/30
target_x = 0.0
target_y = 0.0
target_z = 0.0

prev_time = time.perf_counter()
prev_y = self.browser_window.get_value("positionY")
prev_z = self.browser_window.get_value("positionZ")
prev_x = self.browser_window.get_value("positionX")

while self.run_bot:
    if orientation_tick % orientation_tick_slice == 0: 
        if self.browser_window.get_value("fixedRotationX") > 0 and self.browser_window.get_value("rateRotationX") < (
                min(abs(self.browser_window.get_value("fixedRotationX")), 1) * 2):
            self.browser_window.execute_command("pitchDown")
        if self.browser_window.get_value("fixedRotationX") < 0 and self.browser_window.get_value("rateRotationX") > (
                min(abs(self.browser_window.get_value("fixedRotationX")), 1) * -2):
            self.browser_window.execute_command("pitchUp")
        # Yaw
        if self.browser_window.get_value("fixedRotationY") > 0 and self.browser_window.get_value("rateRotationY") < (
                min(abs(self.browser_window.get_value("fixedRotationY")), 1) * 2):
            self.browser_window.execute_command("yawRight")
        if self.browser_window.get_value("fixedRotationY") < 0 and self.browser_window.get_value("rateRotationY") > (
                min(abs(self.browser_window.get_value("fixedRotationY")), 1) * -2):
            self.browser_window.execute_command("yawLeft")
        # Roll
        if self.browser_window.get_value("fixedRotationY") > 0 and self.browser_window.get_value("rateRotationZ") < (
                min(abs(self.browser_window.get_value("fixedRotationZ")), 1) * 2):
            self.browser_window.execute_command("rollRight")
        if self.browser_window.get_value("fixedRotationZ") < 0 and self.browser_window.get_value("rateRotationZ") > (
                min(abs(self.browser_window.get_value("fixedRotationZ")), 1) * -2):
            self.browser_window.execute_command("rollLeft")
    current_time = time.perf_counter()
    current_y = self.browser_window.get_value("positionY")
    current_z = self.browser_window.get_value("positionZ")
    current_x = self.browser_window.get_value("positionX")
    delta_time = current_time - prev_time
    delta_y = current_y - prev_y
    delta_z = current_z - prev_z
    delta_x = current_x - prev_x
    current_y_speed = delta_y / delta_time
    current_z_speed = delta_z / delta_time
    current_x_speed = delta_x / delta_time
    predicted_y = current_y + (current_y_speed * tick_slice)
    predicted_z = current_z + (current_z_speed * tick_slice)
    predicted_x = current_x + (current_x_speed * tick_slice)
    if translation_tick % translation_tick_slice == 0:
        if predicted_y > target_y and abs(current_y_speed) < .2:
            self.browser_window.execute_command("translateLeft")
        if predicted_y < target_y and abs(current_y_speed) < .2:
            self.browser_window.execute_command("translateRight")
        if predicted_z > target_z and abs(current_z_speed) < .2:
            self.browser_window.execute_command("translateDown")
        if predicted_z < target_z and abs(current_z_speed) < .2:
            self.browser_window.execute_command("translateUp")
        if predicted_x > target_x and abs(current_x_speed) < 2:      
            self.browser_window.execute_command("translateForward")
        if predicted_x < target_x and abs(current_x_speed) < 2:
            self.browser_window.execute_command("translateBackward")
    #  Time delay
    prev_time = current_time
    prev_y = current_y
    prev_z = current_z
    prev_x = current_x
    time.sleep(tick_slice -  (time.perf_counter() - current_time))
    translation_tick += 1
    orientation_tick += 1

print("Bot Loop Stopped.")