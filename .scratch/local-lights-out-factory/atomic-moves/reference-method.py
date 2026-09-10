    def addMoves(self, moves: list[Move]):
        data = [(move.gameid, move.playerid, idx, move.move, move.date)
                for idx, move in enumerate(moves)]
        sql = "INSERT INTO moves(gameid,playerid,idx,move,date) VALUES(?,?,?,?,?)"
        with self.lock:
            try:
                self.conn.executemany(sql, data)
                self.conn.commit()
                return True
            except Error as e:
                self.conn.rollback()
                logger.error("RecorderDb: Unable to add Moves: " + str(e))
                return -1
