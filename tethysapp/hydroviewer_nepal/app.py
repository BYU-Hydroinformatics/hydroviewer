from tethys_sdk.base import TethysAppBase, url_map_maker


class HydroviewerNepal(TethysAppBase):
    """
    Tethys app class for HydroViewer Nepal.
    """

    name = 'HydroViewer Nepal'
    index = 'hydroviewer_nepal:home'
    icon = 'hydroviewer_nepal/images/logo.png'
    package = 'hydroviewer_nepal'
    root_url = 'hydroviewer-nepal'
    color = '#C62E0D'
    description = 'Place a brief description of your app here.'
    tags = 'Hydrology'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='hydroviewer-nepal',
                controller='hydroviewer_nepal.controllers.home'),
            UrlMap(
                name='get-available-dates',
                url='hydroviewer-nepal/ecmwf-rapid/get-available-dates',
                controller='hydroviewer_nepal.controllers.get_available_dates'),
            UrlMap(
                name='get-time-series',
                url='hydroviewer-nepal/ecmwf-rapid/get-time-series',
                controller='hydroviewer_nepal.controllers.ecmwf_get_time_series'),
            UrlMap(
                name='get-return-periods',
                url='hydroviewer-nepal/ecmwf-rapid/get-return-periods',
                controller='hydroviewer_nepal.controllers.get_return_periods'),
            UrlMap(
                name='get-warning-points',
                url='hydroviewer-nepal/ecmwf-rapid/get-warning-points',
                controller='hydroviewer_nepal.controllers.get_warning_points'),
            UrlMap(
                name='get-historic-data',
                url='hydroviewer-nepal/ecmwf-rapid/get-historic-data',
                controller='hydroviewer_nepal.controllers.get_historic_data'),
            UrlMap(
                name='get-flow-duration-curve',
                url='hydroviewer-nepal/ecmwf-rapid/get-flow-duration-curve',
                controller='hydroviewer_nepal.controllers.get_flow_duration_curve'),
            UrlMap(
                name='get_historic_data_csv',
                url='hydroviewer-nepal/ecmwf-rapid/get-historic-data-csv',
                controller='hydroviewer_nepal.controllers.get_historic_data_csv'),
        )

        return url_maps
