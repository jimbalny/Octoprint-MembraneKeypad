# coding=utf-8
from __future__ import absolute_import
import time
import RPi.GPIO as GPIO
from pad4pi import rpi_gpio

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin, settings and asset plugin. Feel free to add or remove mixins
# as necessary.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class MembranekeypadPlugin(octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.StartupPlugin,
					       octoprint.plugin.ShutdownPlugin):

	##~~ SettingsPlugin mixin

	def get_settings_defaults(self):
		return dict(
			# put your plugin's default settings here
			extrudeAmount=5,
			retractAmount=5,
			movementAmount=10,
			movementAmountZ=5,
			cancelDelay=5,
			pRP1=5,
			pRP2=6,
			pRP3=13,
			pRP4=19,
			pCP1=26,
			pCP2=20,
			pCP3=21
			
		)
		
	def get_config_vars(self):
		return dict(
			movementAmount=self._settings.get(["movementAmount"]),
			movementAmountZ=self._settings.get(["movementAmountZ"]),
			extrudeAmount=self._settings.get(["extrudeAmount"]),
			retractAmount=self._settings.get(["retractAmount"]),
			pRP1=self._settings.get(["pRP1"]),
			pRP2=self._settings.get(["pRP2"]),
			pRP3=self._settings.get(["pRP3"]),
			pRP4=self._settings.get(["pRP4"]),
			pCP1=self._settings.get(["pCP1"]),
			pCP2=self._settings.get(["pCP2"]),
			pCP3=self._settings.get(["pCP3"]),
			cancelDelay=self._settings.get(["cancelDelay"])
			
			)
			
	def get_template_configs(self):
		return [
			# dict(type="navbar", custom_bindings=False),
			dict(type="settings", custom_bindings=False)
		]

	def on_settings_save(self, data):
		octoprint.plugin.SettingsPlugin.on_settings_save(self, data)

	##~~ AssetPlugin mixin

	def get_assets(self):
		# Define your plugin's asset files to automatically include in the
		# core UI here.
		return dict(
			js=["js/membranekeypad.js"],
			css=["css/membranekeypad.css"],
			less=["less/membranekeypad.less"]
		)

	##~~ Softwareupdate hook

	def get_update_information(self):
		# Define the configuration for your plugin to use with the Software Update
		# Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
		# for details.
		return dict(
			membranekeypad=dict(
				displayName="Membranekeypad Plugin",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="jimbalny",
				repo="OctoPrint-Membranekeypad",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/jimbalny/OctoPrint-Membranekeypad/archive/{target_version}.zip"
			)
		)

	def on_after_startup(self):
		self.start_keypad_thread()
		
	def on_shutdown(self):
		self.stop_keypad_thread()
		self._logger.info("Plugin Shutdown, Clean Up GPIO")
		
	def start_keypad_thread(self):
		conf = self.get_config_vars()
		
		# Import Settings
		self.RP1 = self._settings.get(["pRP1"])
		self.RP2 = self._settings.get(["pRP2"])
		self.RP3 = self._settings.get(["pRP3"])
		self.RP4 = self._settings.get(["pRP4"])
		self.CP1 = self._settings.get(["pCP1"])
		self.CP2 = self._settings.get(["pCP2"])
		self.CP3 = self._settings.get(["pCP3"])

		GPIO.setwarnings(False)
		
		# Keypad Buttons Definition
		KPad = [[1, 2, 3], [4, 5, 6], [7, 8, 9], ['*', 0, '#']] 

		Row_Pins = [self.RP1, self.RP2, self.RP3, self.RP4]
		Col_Pins = [self.CP1, self.CP2, self.CP3]
		#ROW_PINS = [5, 6, 13, 19]
		#COL_PINS = [26, 20, 21]
		
		try:
			self._logger.info(KPad + Row_Pins + Col_Pins)
			factory = rpi_gpio.KeypadFactory()
			keypad = factory.create_keypad(keypad=KPad, row_pins=Row_Pins, col_pins=Col_Pins)
			keypad.registerKeyPressHandler(self.pressKey)
			
			while True:
				time.sleep(1)
				
		except:
			self._logger.info("Error Initializing Keypad!")
			
		finally:
			self._logger.info("GPIO Cleanup")
			keypad.cleanup()
		
	def pressKey(self, key):
		self.movementMM = self._settings.get(["movementAmount"])
		self.movementMMZ = self._settings.get(["movementAmountZ"])
		self.extrudeMM = self._settings.get(["extrudeAmount"])
		self.retractMM = self._settings.get(["retractAmount"])
		self.cancelDelay = self._settings.get(["cancelDelay"])
		
		if key == 6:
			self.getPrinterObject().jog(dict(x=self.movementMM))
		elif key == 4:
			self.getPrinterObject().jog(dict(x="-" + str(self.movementMM)))
		elif key == 2:
			self.getPrinterObject().jog(dict(y="-" + str(self.movementMM)))
		elif key == 5:
			self.getPrinterObject().jog(dict(y=self.movementMM))
		elif key == 1:
			self.getPrinterObject().jog(dict(z=self.movementMMZ))
		elif key == 3:
			self.getPrinterObject().jog(dict(z="-" + str(self.movementMMZ)))
		elif key == 8:
			self.getPrinterObject().extrude(-self.retractMM)
		elif key == 9:
			self.getPrinterObject().extrude(self.extrudeMM)
		elif key == "#":
			time.sleep(int(self.cancelDelay))
			if key == "#":
				self.getPrinterObject().cancel_print()
		elif key == "*":
			if self.getPrinterObject().get_state_id == "PAUSED":
				self.getPrinterObject().resume_print()
			elif self.getPrinterObject().get_state_id == "PRINTING":
				self.getPrinterObject().pause_print()
			elif self.getPrinterObject().get_state_id == "OPERATIONAL":
				self.getPrinterObject().start_print()
	
	def stop_keypad_thread(self):
		self.keypad.cleanup()
		
	# Misc:
	
	def getPrinterObject(self):
		return self._printer
		
	def getLogger(self):
		return self._logger

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Membrane Keypad Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = MembranekeypadPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
