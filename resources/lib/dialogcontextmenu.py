
import xbmc, xbmcgui, xbmcaddon

import util, nfowriter, wizardconfigxml, helper
import dialogeditromcollection, dialogeditscraper, dialogdeleteromcollection, config
from nfowriter import *
from gamedatabase import *
from util import *
from config import *
from util import Logutil as log

ACTION_CANCEL_DIALOG = (9, 10, 51, 92, 110)
CONTROL_BUTTON_SETFAVORITE_GAME = 5118
CONTROL_BUTTON_SETFAVORITE_SELECTION = 5119


class ContextMenuDialog(xbmcgui.WindowXMLDialog):
		
	selectedGame = None
	gameRow = None
		
	def __init__(self, *args, **kwargs):
		# Don't put GUI sensitive stuff here (as the xml hasn't been read yet)
		log.info("init ContextMenu")
		
		self.gui = kwargs["gui"]
		
		self.doModal()
	
	def onInit(self):
		log.info("onInit ContextMenu")
		
		pos = self.gui.getCurrentListPosition()
		if pos != -1:
			self.selectedGame, self.gameRow = self.gui.getGameByPosition(self.gui.gdb, pos)
			
		# Set mark favorite text
		if self.gameRow is not None:
			if self.gameRow[util.GAME_isFavorite] == 1:
				buttonMarkFavorite = self.getControlById(CONTROL_BUTTON_SETFAVORITE_GAME)
				if buttonMarkFavorite is not None:
					buttonMarkFavorite.setLabel(util.localize(32133))
				buttonMarkFavorite = self.getControlById(CONTROL_BUTTON_SETFAVORITE_SELECTION)
				if buttonMarkFavorite is not None:
					buttonMarkFavorite.setLabel(util.localize(32134))
		
		# Hide Set Gameclient option
		if not helper.retroPlayerSupportsPythonIntegration():
			control = self.getControlById(5224)
			control.setVisible(False)
			control.setEnabled(False)
	
	def onAction(self, action):
		if (action.getId() in ACTION_CANCEL_DIALOG):
			self.close()
	
	def onClick(self, controlID):
		if controlID == 5101:  # Close window button
			self.close()
		elif controlID == 5110:  # Import games
			self.close()
			self.gui.updateDB()
		elif controlID == 5121:  # Rescrape single games
			self.close()
			
			if self.selectedGame is None or self.gameRow is None:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32013), util.localize(32014))
				return
			
			romCollectionId = self.gameRow[util.GAME_romCollectionId]
			romCollection = self.gui.config.romCollections[str(romCollectionId)]
			files = File(self.gui.gdb).getRomsByGameId(self.gameRow[util.ROW_ID])
			filename = files[0][0]
			romCollection.romPaths = (filename,)
						
			romCollections = {}
			romCollections[romCollection.id] = romCollection
			
			self.gui.rescrapeGames(romCollections)
			
		elif controlID == 5122:  # Rescrape selection
			self.close()
			
			romCollections = {}
			listSize = self.gui.getListSize()
			for i in range(0, listSize):
				selectedGame, gameRow = self.gui.getGameByPosition(self.gui.gdb, i)
				
				romCollectionId = gameRow[util.GAME_romCollectionId]
				
				try:
					romCollection = romCollections[str(romCollectionId)]
				except:				
					romCollection = self.gui.config.romCollections[str(romCollectionId)]
					romCollection.romPaths = []
					
				files = File(self.gui.gdb).getRomsByGameId(gameRow[util.ROW_ID])
				try:
					filename = files[0][0]
					romCollection.romPaths.append(filename)
					romCollections[romCollection.id] = romCollection
				except:
					log.info("Error getting filename for romCollectionId: {0}".format(romCollectionId))

			self.gui.rescrapeGames(romCollections)

			#self.gui.updateDB()
		elif controlID == 5111:  # Add Rom Collection
			self.close()
			statusOk, errorMsg = wizardconfigxml.ConfigXmlWizard().addRomCollection(self.gui.config)
			if statusOk is False:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32001), errorMsg)
				log.info("Error updating config.xml: {0}".format(errorMsg))
				return
			
			#update self.config
			statusOk, errorMsg = self.gui.config.readXml()
			if statusOk is False:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32002), errorMsg)
				log.info("Error reading config.xml: {0}".format(errorMsg))
				return
			
			#import Games
			self.gui.updateDB()
			
		elif controlID == 5112:  # Edit Rom Collection
			self.close()
			constructorParam = "720p"
			editRCdialog = dialogeditromcollection.EditRomCollectionDialog("script-RCB-editromcollection.xml", util.getAddonInstallPath(), "Default", constructorParam, gui=self.gui)			
			del editRCdialog
			
			self.gui.config = Config(None)
			self.gui.config.readXml()
			
		elif controlID == 5117:  # Edit scraper
			self.close()			
			constructorParam = "720p"
			editscraperdialog = dialogeditscraper.EditOfflineScraper("script-RCB-editscraper.xml", util.getAddonInstallPath(), "Default", constructorParam, gui=self.gui)			
			del editscraperdialog
			
			self.gui.config = Config(None)
			self.gui.config.readXml()
		
		elif controlID == 5113:  # Edit Game Command
			self.close()
			
			if(self.selectedGame == None or self.gameRow == None):
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32015), util.localize(32014))
				return

			origCommand = self.gameRow[util.GAME_gameCmd]
			command = ''
									
			keyboard = xbmc.Keyboard()
			keyboard.setHeading(util.localize(32135))
			if origCommand is not None:
				keyboard.setDefault(origCommand)
			keyboard.doModal()
			if keyboard.isConfirmed():
				command = keyboard.getText()
					
			if command != origCommand:
				log.info("Updating game '{0}' with command '{1}'".format(self.gameRow[util.ROW_NAME], command))
				Game(self.gui.gdb).update(('gameCmd',), (command,), self.gameRow[util.ROW_ID], True)
				self.gui.gdb.commit()
				
		elif controlID == 5118:  # (Un)Mark as Favorite
			self.close()
						
			if self.selectedGame is None or self.gameRow is None:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32016), util.localize(32014))
				return
						
			isFavorite = 1
			if self.gameRow[util.GAME_isFavorite] == 1:
				isFavorite = 0

			log.info("Updating game '{0}' set isFavorite = {1}".format(self.gameRow[util.ROW_NAME], isFavorite))
			Game(self.gui.gdb).update(('isFavorite',), (isFavorite,), self.gameRow[util.ROW_ID], True)
			self.gui.gdb.commit()
						
			if isFavorite == 0:
				isFavorite = ''
			self.selectedGame.setProperty('isfavorite', str(isFavorite))
			
		elif controlID == 5119:  # (Un)Mark as Favorite
			self.close()
						
			if self.selectedGame is None or self.gameRow is None:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32016), util.localize(32014))
				return
						
			isFavorite = 1
			if self.gameRow[util.GAME_isFavorite] == 1:
				isFavorite = 0
			
			listSize = self.gui.getListSize()
			for i in range(0, listSize):
				
				selectedGame, gameRow = self.gui.getGameByPosition(self.gui.gdb, i)

				log.info("Updating game '{0}' set isFavorite = {1}".format(gameRow[util.ROW_NAME], isFavorite))
				Game(self.gui.gdb).update(('isFavorite',), (isFavorite,), gameRow[util.ROW_ID], True)
				selectedGame.setProperty('isfavorite', str(isFavorite))
			self.gui.gdb.commit()
			
			#HACK: removing favorites does not update the UI. So do it manually.
			if isFavorite == 0:
				self.gui.loadViewState()			
			
		elif controlID == 5120:  # Export nfo files
			self.close()
			nfowriter.NfoWriter().exportLibrary(self.gui)
			
		elif controlID == 5114:  # Delete Rom
			self.close()
			
			pos = self.gui.getCurrentListPosition()
			if pos == -1:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32017), util.localize(32018))
				return					
			dialog = xbmcgui.Dialog()
			if dialog.yesno(util.localize(32510), util.localize(32136)):
				gameID = self.gui.getGameId(self.gui.gdb, pos)
				self.gui.deleteGame(gameID)
				self.gui.showGames()
				if pos > 0:
					pos = pos - 1
					self.gui.setFilterSelection(self.gui.CONTROL_GAMES_GROUP_START, pos)
				else:
					self.gui.setFilterSelection(self.gui.CONTROL_GAMES_GROUP_START, 0)
		
		elif controlID == 5115:  # Remove Rom Collection
			self.close()
						
			constructorParam = "720p"
			removeRCDialog = dialogdeleteromcollection.RemoveRCDialog("script-RCB-removeRC.xml", util.getAddonInstallPath(), "Default", constructorParam, gui=self.gui)			
			rDelStat = removeRCDialog.getDeleteStatus()
			if rDelStat:
				selectedRCId = removeRCDialog.getSelectedRCId()
				rcDelStat = removeRCDialog.getRCDeleteStatus()
				self.gui.deleteRCGames(selectedRCId, rcDelStat, rDelStat)
				del removeRCDialog
				
		elif controlID == 5116:  # Clean DB
			self.close()
			self.gui.cleanDB()
				
		elif controlID == 5223:  # Open Settings
			self.close()			
			self.gui.Settings.openSettings()
		
		elif controlID == 5224:  # Set gameclient
			self.close()
			
			if not helper.retroPlayerSupportsPythonIntegration():
				log.info("This RetroPlayer branch does not support selecting gameclients.")
				return
			
			if self.selectedGame is None or self.gameRow is None:
				xbmcgui.Dialog().ok(util.SCRIPTNAME, util.localize(32015), util.localize(32014))
				return

			#HACK: use alternateGameCmd to store gameclient information
			origGameClient = self.gameRow[util.GAME_alternateGameCmd]
			gameclient = ''
			
			romCollectionId = self.gameRow[util.GAME_romCollectionId]
			romCollection = self.gui.config.romCollections[str(romCollectionId)]
						
			success, selectedcore = helper.selectlibretrocore(romCollection.name)
			if success:
				gameclient = selectedcore
			else:
				log.info("No libretro core was chosen. Won't update game command.")
				return
				
			if gameclient != origGameClient:
				log.info("Updating game '{0}' with gameclient '{1}'".format(self.gameRow[util.ROW_NAME], gameclient))
				Game(self.gui.gdb).update(('alternateGameCmd',), (gameclient,), self.gameRow[util.ROW_ID], True)
				self.gui.gdb.commit()
	
	def onFocus(self, controlID):
		pass

	def getControlById(self, controlId):
		try:
			control = self.getControl(controlId)
		except Exception, (exc):
			return None
		
		return control
