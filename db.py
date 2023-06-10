import sqlite3


class BotDB:

    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()

    def get_users(self):
        result = self.cursor.execute("SELECT * FROM `users`")
        return result.fetchall()

    def user_exists(self, user_id):
        """Проверяем, есть ли юзер в базе"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(len(result.fetchall()))

    def get_user_id(self, user_id):
        """Достаем id юзера в базе по его user_id"""
        result = self.cursor.execute("SELECT `id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def get_user_stage(self, user_id):
        """Достаём этап"""
        result = self.cursor.execute("SELECT `stage` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def is_admin(self, user_id):
        """Достаём булевное"""
        result = self.cursor.execute("SELECT `admin` FROM `users` WHERE `user_id` = ?", (user_id,))
        return bool(result.fetchone()[0])

    def get_username(self, user_id):
        result = self.cursor.execute("SELECT `name` FROM `users` WHERE `user_id` = ?", (user_id,))
        fetchone = result.fetchone()
        #print(fetchone, end='')
        if fetchone is not None:
            #print(f'Возврат {fetchone[0]}')
            return fetchone[0]
        else:
            #print('Возврат virtual')
            return f'virtual{user_id}'

    def get_game(self, user_id):
        """Достаём игру"""
        result = self.cursor.execute("SELECT `game_id` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def get_wins(self, user_id):
        """Достаём колиество побед"""
        result = self.cursor.execute("SELECT `num_wins` FROM `users` WHERE `user_id` = ?", (user_id,))
        return result.fetchone()[0]

    def set_admin(self, user_id):
        """Устанавливаем админа"""
        self.cursor.execute("UPDATE `users` SET `admin` = 1 WHERE `user_id` = ?", (user_id,))
        return self.conn.commit()

    def set_stage(self, user_id, stage):
        """Устанавливаем стадию"""
        self.cursor.execute("UPDATE `users` SET `stage` = ? WHERE `user_id` = ?", (stage, user_id))
        return self.conn.commit()

    def set_wins(self, user_id, wins):
        """Устанавливаем количество побед"""
        self.cursor.execute("UPDATE `users` SET `num_wins` = ? WHERE `user_id` = ?", (wins, user_id))
        return self.conn.commit()

    def set_name(self, user_id, name):
        """Устанавливаем имя"""
        self.cursor.execute("UPDATE `users` SET `name` = ? WHERE `user_id` = ?", (name, user_id))
        return self.conn.commit()

    def set_game(self, user_id, game_id):
        """Устанавливаем игру"""
        self.cursor.execute("UPDATE `users` SET `game_id` = ? WHERE `user_id` = ?", (game_id, user_id))
        return self.conn.commit()

    def add_user(self, user_id, stage=0, name="default", wins=0):
        """Добавляем юзера в базу"""
        self.cursor.execute(
            "INSERT INTO `users` (`user_id`, `stage`, `admin`, `name`, `game_id`, `num_wins`) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, stage, 0, name, -1, wins))
        return self.conn.commit()

    def del_user(self, user_id):
        self.cursor.execute("DELETE FROM `users` WHERE `user_id` = ?", (user_id,))
        return self.conn.commit()

    def close(self):
        """Закрываем соединение с БД"""
        self.conn.close()
