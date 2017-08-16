import numpy as np
from MineSweeper import MineSweeper
import time

class MineSweeperLearner:
    def __init__(self, model, dim):
        self.model = model
        self.dim = dim
        self.totalCells = dim * dim

    # ultimately want to put this in the model so each can extract its own shit
    def getPredictorsFromGameState(self, state):
        out = np.zeros((1, 10, self.dim, self.dim))
        # channel 0: cell is still available
        out[0][0] = np.where(np.isnan(state), 0, 1)
        # the numeric channels: categories from 0 to 8
        for i in range(0, 9):
            out[0][i + 1] = np.where(state == i, 1, 0)
        return out

    def learnMineSweeper(self, gamesPerBatch, nBatches, verbose=True):
        for i in range(nBatches):
            X = np.zeros((1, 10, self.dim, self.dim))  # 10 channels: 1 for each number, 1 for if has been revealed
            X2 = np.zeros((1, 1, self.dim, self.dim))
            y = np.zeros((1, 1, self.dim, self.dim))
            meanCellsRevealed = 0
            propGamesWon = 0
            for j in range(gamesPerBatch):
                # initiate game
                game = MineSweeper(self.dim, int(0.2 * self.totalCells))
                while not game.gameOver:
                    # get data input from game state
                    Xnow = self.getPredictorsFromGameState(game.state)
                    X = np.append(X, Xnow, 0)
                    X2now = np.array([[np.where(Xnow[0][0] == 0, 1, 0)]])
                    X2 = np.append(X2, X2now, 0)
                    # make probability predictions
                    out = self.model.predict([Xnow, X2now])
                    # choose best remaining cell
                    orderedProbs = np.argsort(out[0][0]+Xnow[0][0], axis=None) #add Xnow[0] so that already selected cells aren't chosen
                    selected = orderedProbs[0]
                    selectedX = int(selected / self.dim)
                    selectedY = selected % self.dim
                    game.selectCell((selectedX, selectedY))
                    # find truth
                    truth = out
                    truth[0, 0, selectedX, selectedY] = game.mines[selectedX, selectedY]
                    y = np.append(y, truth, 0)
                meanCellsRevealed += self.totalCells - np.sum(np.isnan(game.state))
                if game.victory:
                    propGamesWon += 1
            meanCellsRevealed = float(meanCellsRevealed) / gamesPerBatch
            propGamesWon = float(propGamesWon) / gamesPerBatch
            if verbose:
                print "Mean cells revealed, batch " + str(i) + ": " + str(meanCellsRevealed)
                print "Proportion of games won, batch " + str(i) + ": " + str(propGamesWon)
            # now train on data
            X = np.delete(X, 0, 0)
            X2 = np.delete(X2, 0, 0)
            y = np.delete(y, 0, 0)
            # print y
            self.model.fit([X, X2], y, epochs=1)