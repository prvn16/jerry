from PyQt4.QtGui import *
from PyQt4.QtCore import *
#import chess
from chess.polyglot import *
from dialogs.dialog_browse_pgn import DialogBrowsePgn
from model.database import Database
import controller
import model.gamestate

class FileMenuController():

    def __init__(self, mainAppWindow, model):
        super(FileMenuController, self).__init__()
        self.mainAppWindow = mainAppWindow
        self.model = model

    def print_game(self):
        gamestate = self.model.gamestate
        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            exporter = chess.pgn.StringExporter()
            gamestate.current.root().export(exporter, headers=True, variations=True, comments=True)
            pgn = str(exporter)
            QPgn = QPlainTextEdit(pgn)
            QPgn.print_(dialog.printer())

    def print_position(self):
        q_widget = self.mainAppWindow
        dialog = QPrintDialog()
        if dialog.exec_() == QDialog.Accepted:
            p = QPixmap.grabWindow(q_widget.winId())
            painter = QPainter(dialog.printer())
            dst = QRect(0,0,200,200)
            painter.drawPixmap(dst, p)
            del painter

    def save_image(self):
        q_widget = self.mainAppWindow
        filename = QFileDialog.getSaveFileName(q_widget, q_widget.trUtf8('Save Image'), None, 'JPG (*.jpg)', QFileDialog.DontUseNativeDialog)
        if(filename):
            p = QPixmap.grabWindow(q_widget.chessboard_view.winId())
            p.save(filename,'jpg')

    def save(self):
        mainWidget = self.mainAppWindow
        db = mainWidget.model.database
        # if the game is not in the database
        # i.e. hasn't been saved yet, then
        # calls save_as
        if(db.index_current_game == None):
            self.save_as_new()
        else:
            db.update_game(db.index_current_game,mainWidget.model.gamestate.current)
        mainWidget.save.setEnabled(False)
        mainWidget.moves_edit_view.setFocus()

    def save_as_new(self):
        mainWidget = self.mainAppWindow
        db = mainWidget.model.database
        gs = mainWidget.model.gamestate
        # let the user enter game data
        controller.edit.editGameData(mainWidget)
        db.append_game(gs.current)
        mainWidget.save.setEnabled(False)
        mainWidget.moves_edit_view.setFocus()


    def save_db_as_new(self):
        mainWidget = self.mainAppWindow
        gs = mainWidget.gs
        db = mainWidget.database
        dialog = QFileDialog()
        if(gs.last_save_dir != None):
            dialog.setDirectory(gs.last_save_dir)
        filename = dialog.getSaveFileName(mainWidget, mainWidget.trUtf8('Save PGN'), None, 'PGN (*.pgn)', QFileDialog.DontUseNativeDialog)
        if(filename):
            if(not filename.endswith(".pgn")):
                filename = filename + ".pgn"
            db.save_as_new(mainWidget, filename)
            mainWidget.user_settings.active_database = db.filename
            mainWidget.save.setEnabled(False)
            mainWidget.movesEdit.setFocus()
            gs.last_save_dir = QFileInfo(filename).dir().absolutePath()



    def export_game(self):
        mainWidget = self.mainAppWindow
        gamestate = mainWidget.gs
        dialog = QFileDialog()
        if(gamestate.last_save_dir != None):
            dialog.setDirectory(gamestate.last_save_dir)
        filename = dialog.getSaveFileName(mainWidget, mainWidget.trUtf8('Save PGN'), None, 'PGN (*.pgn)', QFileDialog.DontUseNativeDialog)
        if(filename):
            if(not filename.endswith(".pgn")):
                filename = filename + ".pgn"
            f = open(filename,'w')
            print(gamestate.current.root(), file=f, end="\n\n")
            gamestate.pgn_filename = filename
            #mainWidget.save_game.setEnabled(True)
            mainWidget.movesEdit.setFocus()
            f.close()
            gamestate.last_save_dir = QFileInfo(filename).dir().absolutePath()

    def save_to_db(self):
        mainWindow = self.mainAppWindow
        mainWindow.database.add_current_game(mainWindow.gs.game.root())
        mainWindow.save_in_db.setEnabled(False)

    def init_game_tree(self,root):
        mainWindow = self.mainAppWindow
        gamestate = mainWindow.model.gamestate
        # ugly workaround:
        # the next lines are just to ensure that
        # the "board cache" (see doc. of python-chess lib)
        # is initialized. The call to the last board of the main
        # line ensures recursive calls to the boards up to
        # the root
        temp = gamestate.current.root()
        end = gamestate.current.end()
        mainline_nodes = [temp]
        while(not temp == end):
            temp = temp.variations[0]
            mainline_nodes.append(temp)
        cnt = len(mainline_nodes)
        pDialog = QProgressDialog(mainWindow.trUtf8("Initializing Game Tree"),None,0,cnt,mainWindow)
        pDialog.setWindowModality(Qt.WindowModal)
        pDialog.show()
        QApplication.processEvents()
        for i,n in enumerate(mainline_nodes):
            QApplication.processEvents()
            pDialog.setValue(i)
            if(i > 0 and i % 25 == 0):
                _ = n.cache_board()
        pDialog.close()

    def new_database(self):
        mainWindow = self.mainAppWindow
        dialog = QFileDialog()
        ret = controller.gameevents.unsaved_changes(mainWindow)
        if not ret == QMessageBox.Cancel:
            filename = dialog.getSaveFileName(mainWindow, mainWindow.trUtf8('Create New PGN'), None, 'PGN (*.pgn)', QFileDialog.DontUseNativeDialog)
            if(filename):
                if(not filename.endswith(".pgn")):
                    filename = filename + ".pgn"
                #with open(filename,'w') as pgn:
                #    print(mainWindow.gs.current.root(), file=pgn, end="\n\n")
                #    mainWindow.save_game.setEnabled(True)
                #    mainWindow.movesEdit.setFocus()
                mainWindow.model.gamestate.last_save_dir = QFileInfo(filename).dir().absolutePath()
                db = Database(filename)
                db.create_new_pgn()
                mainWindow.save.setEnabled(False)
                mainWindow.model.database = db
                mainWindow.model.user_settings.active_database = db.filename

    def open_pgn(self):
        mainWindow = self.mainAppWindow
        chessboardview = mainWindow.chessboard_view
        gamestate = mainWindow.model.gamestate
        dialog = QFileDialog()
        if(gamestate.last_open_dir != None):
            dialog.setDirectory(gamestate.last_open_dir)
        filename = dialog.getOpenFileName(chessboardview, mainWindow.trUtf8('Open PGN'), None, 'PGN (*.pgn)',QFileDialog.DontUseNativeDialog)
        if filename:
            db = Database(filename)
            db.init_from_file(mainWindow,mainWindow.trUtf8("Scanning PGN File..."))
            mainWindow.model.database = db
            mainWindow.model.user_settings.active_database = db.filename
            selectedGame = 0
            if(db.no_of_games() > 1):
                dlg = DialogBrowsePgn(db)
                if dlg.exec_() == QDialog.Accepted:
                    items = dlg.table.selectedItems()
                    selectedGame = int(items[0].text())-1
                else:
                    selectedGame = None
            if(not selectedGame == None):
                loaded_game = db.load_game(selectedGame)
                    #offset, headers = db.offset_headers[idx]
                    #pgn.seek(offset)
                    #first_game = chess.pgn.read_game(pgn)
                gamestate.current = loaded_game
                chessboardview.update()
                chessboardview.emit(SIGNAL("statechanged()"))
                mainWindow.save.setEnabled(False)
                mainWindow.setLabels()
                mainWindow.moves_edit_view.setFocus()
                gamestate.last_open_dir = QFileInfo(filename).dir().absolutePath()
                self.init_game_tree(gamestate.current.root())

                    #if(dlg.table.hasS)
                    #print(str(dlg.table.selectedIndexes()))


        """
        if(filename):
            pgn = open(filename)
            first_game = chess.pgn.read_game(pgn)
            gamestate.current = first_game
            chessboardview.update()
            chessboardview.emit(SIGNAL("statechanged()"))
            gamestate.pgn_filename = filename
            mainWindow.save_game.setEnabled(True)
            mainWindow.setLabels()
            mainWindow.movesEdit.setFocus()
            pgn.close()
            gamestate.last_open_dir = QFileInfo(filename).dir().absolutePath()
            init_game_tree(mainWindow,gamestate.current.root())
        """

    def browse_database(self):
        mainWindow = self.mainAppWindow
        selectedGame = 0
        mainWindow.model.gamestate.mode = model.gamestate.MODE_ENTER_MOVES
        db = mainWindow.model.database
        gs = mainWindow.model.gamestate
        cbv = mainWindow.chessboard_view

        dlg = DialogBrowsePgn(db)
        #
        if dlg.exec_() == QDialog.Accepted:
            items = dlg.table.selectedItems()
            selectedGame = int(items[0].text())-1
            loaded_game = db.load_game(selectedGame)
            #offset, headers = db.offset_headers[idx]
            #pgn.seek(offset)
            #first_game = chess.pgn.read_game(pgn)
            print("loaded game: "+str(loaded_game))
            if(not loaded_game == None):
                ret = controller.gameevents.unsaved_changes(mainWindow)
                if not ret == QMessageBox.Cancel:
                    gs.current = loaded_game
                    cbv.update()
                    cbv.emit(SIGNAL("statechanged()"))
                    gs.unsaved_changes = False
                    mainWindow.save.setEnabled(False)
                    mainWindow.setLabels()
                    mainWindow.moves_edit_view.setFocus()
                    self.init_game_tree(gs.current.root())


    def is_position_in_book(self,node):
        with open_reader("./books/varied.bin") as reader:
            entries = reader.get_entries_for_position(node.board())
            moves = []
            for entry in entries:
                move = entry.move().uci()
                moves.append(move)
            l = len(moves)
            if(l > 0):
                return True
            else:
                return False