from MVCModel import Model, View, Control

if __name__ == "__main__":

    view = View()
    model = Model()
    control = Control()

    view.set_model(model)
    view.set_control(control)
    model.set_view(view)
    control.set_model(model)

    view.update()
