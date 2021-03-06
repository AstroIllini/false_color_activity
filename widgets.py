import os
import copy
from catalog import Catalog
from image import Image, ImageLayer
import ipywidgets as widgets
from ipywidgets import interact, interactive
import matplotlib.pyplot as plt
from IPython.display import display, clear_output


catalog = Catalog(os.path.join("data", "catalog.yml"))
skip_layer_plot = False


def get_layer_widget(layer, plot_function=None):
    color = widgets.ColorPicker(concise=False, description='Layer color',
                                value=layer.color, disabled=False)
    alpha = widgets.FloatSlider(value=1.0, min=0, max=1.0, continuous_update=False,
                                description='Opacity', readout=True)
    logscale = widgets.Checkbox(value=False, description='Logarithmic scaling')
    def wrapper(**kwargs):
        layer.update(object_name=layer.object, filter_name=layer.filter, **kwargs)
        if (plot_function is not None) and (not skip_layer_plot):
            plot_function()
    w = interactive(wrapper, color=color, alpha=alpha, logscale=logscale)
    return w


def get_image_widget():
    w_out = widgets.Output(layout=widgets.Layout(width='50%'))
    w_layers = widgets.Accordion()
    fullres_box = widgets.Checkbox(
        value=False, description='Display full resolution (slow)')
    figwidth_box = widgets.BoundedFloatText(
        value=10, min=1, max=1000,
        description='Width (cm)')
    def wrapper(object_name):
        if object_name.startswith('*'):
            print('Downloading fits files, this may take a few minutes.')
            object_name = object_name.strip('*')
        obj = Image(object_name, catalog=catalog)
        obj.widget_setup_complete = False
        def plot_function(change=None):
            if not obj.widget_setup_complete:
                return
            w_out.clear_output()
            with w_out:
                obj.plot(fullres=fullres_box.value,
                         figsize=(figwidth_box.value,
                                  figwidth_box.value))
        fullres_box.observe(plot_function, names='value')
        figwidth_box.observe(plot_function, names='value')
        w_clr = []
        extra_colors = ['magenta', 'cyan', 'yellow', 'orange',
                        'purple', 'pink', 'turquoise', 'lavender']
        if 'optical_red' not in obj.filters:
            extra_colors = obj.default_colors + extra_colors
        for x in obj.filters:
            if x.split('optical_')[-1] in obj.default_colors:
                clr = x.split('optical_')[-1]
            else:
                clr = extra_colors.pop(0)
            new_layer = ImageLayer(object_name=obj.object,
                                   filter_name=x, color=clr,
                                   catalog=obj.catalog)
            obj.append_layer(new_layer)
            w_clr.append(get_layer_widget(new_layer, plot_function=plot_function))
        w_layers.children = w_clr
        for i, x in enumerate(obj.filters):
            w_layers.set_title(i, x)
        obj.widget_setup_complete = True
        plot_function()
    object_list = catalog.local_objects + ['*' + x for x in catalog.remote_objects]
    w = interactive(wrapper,
                    object_name=widgets.Dropdown(
                        options=object_list, value='kepler',
                        description='Object', disabled=False))
    w_control = widgets.VBox([w, figwidth_box, fullres_box, w_layers],
                             layout=widgets.Layout(width='50%'))
    w_all = widgets.HBox([w_control, w_out])
    return w_all


def ImageWidget():
    global skip_layer_plot
    skip_layer_plot = True
    w = get_image_widget()
    display(w)
    skip_layer_plot = False
