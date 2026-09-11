def create_new_room_action(self):
    pass


def join_room_action(self):
    pass


def deck_editor_action(self, deck_build_action_button_name):
    # New Button
    self.new_deck_btn = ctk.CTkButton(self, text="DECKS", font=("Kanisah", 20, "bold"), command=self.new_deck_action)
    self.new_deck_btn.pack(pady=10, padx=20)

    # Second Action Button
    self.second_deck_action_btn = ctk.CTkButton(self, text=deck_build_action_button_name, font=("Kanisah", 20, "bold"),
                                                command=self.second_deck_editor_action)
    self.second_deck_action_btn.pack(pady=10, padx=20)


def new_deck_btn(self):
    pass


def second_deck_action_btn(self, deck_build_action_button_name):
    if deck_build_action_button_name = "Edit":
    # do the action for edit
    else:
# do teh action for load