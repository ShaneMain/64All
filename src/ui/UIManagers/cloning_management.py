class CloningFinishHandler:
    def __init__(self, ui_setup):
        self.ui_setup = ui_setup

    def cloning_finished(self, success):
        if success:
            self.ui_setup.output_text_manager.update_output_text("[32mCloning finished successfully![0m\n")
            self.ui_setup.output_text_manager.update_output_text("[32mStarting build process...[0m\n")
            self.ui_setup.parent.build_manager.start_building()
        else:
            self.ui_setup.output_text_manager.update_output_text("[31mCloning failed. Check the output for errors.[0m\n")
            self.ui_setup.output_text_manager.update_output_text("[33mYou may need to try cloning again.[0m\n")