import numpy as np


class FluxRelaxation(object):
    """Decorator that adds time dependence to fluxes
    Simple relaxation on a fixed timescale
    """

    def __init__(self, fluxModel, timescale):
        """
        Inputs:
          fluxModel        fluxmodel to be decorated.
                           Should have a get_flux(profiles) method which takes
                           a dictionary input and returns a dictionary of fluxes
          timescale        Ratio of flux relaxation timescale to coupling period
        """
        assert hasattr(fluxModel, "get_flux") and callable(
            getattr(fluxModel, "get_flux")
        )
        assert timescale > 0.0

        self.fluxModel = fluxModel
        # Weight between 0 and 1 on last fluxes (-> 0 as timescale becomes shorter)
        self.weight = np.exp(-1.0 / timescale)
        self.lastFluxes = None  # No previous flux

    def get_flux(self, profiles):
        # Call the flux model to get the new flux
        newFluxes = self.fluxModel.get_flux(profiles)
        if self.lastFluxes is None:
            self.lastFluxes = newFluxes

        # Apply relaxation to each flux channel
        for key in newFluxes:
            newFluxes[key] = (
                self.weight * self.lastFluxes[key]
                + (1.0 - self.weight) * newFluxes[key]
            )

        self.lastFluxes = newFluxes
        return newFluxes


class FluxDoubleRelaxation(object):
    """Decorator that adds time dependence to fluxes, with two timescales:
    one timescale for the drive, and one for the damping.
    """

    def __init__(self, fluxModel, turb_timescale, damp_timescale):
        """
        Inputs:
          fluxModel
              fluxmodel to be decorated.
              Should have a get_flux(profiles) method which takes
              a dictionary input and returns a dictionary of fluxes
          turb_timescale
              Ratio of flux relaxation timescale to coupling period
          damp_timescale
              Ratio of damping timescale to coupling period
        """
        assert hasattr(fluxModel, "get_flux") and callable(
            getattr(fluxModel, "get_flux")
        )
        assert turb_timescale > 0.0
        assert damp_timescale > 0.0

        self.fluxModel = fluxModel
        # Weight between 0 and 1 on last fluxes (-> 0 as timescale becomes shorter)
        self.turb_weight = np.exp(-1.0 / turb_timescale)
        self.damp_weight = np.exp(-1.0 / damp_timescale)
        self.lastTurb = None  # No previous turbulent drive or damping
        self.lastDamp = None

    def get_flux(self, profiles):
        # Call the flux model to get the new flux
        newFluxes = self.fluxModel.get_flux(profiles)
        if self.lastTurb is None:
            # Shallow copies of the flux dictionary
            self.lastTurb = newFluxes.copy()
            self.lastDrive = newFluxes.copy()

        # Apply relaxation to each flux channel
        for key in newFluxes:
            # Relax both turbulence drive and damping towards new fluxes
            self.lastTurb[key] = (
                self.turb_weight * self.lastTurb[key]
                + (1.0 - self.turb_weight) * newFluxes[key]
            )
            self.lastDrive[key] = (
                self.damp_weight * self.lastDrive[key]
                + (1.0 - self.damp_weight) * newFluxes[key]
            )
            # Calculate a ratio which goes towards the input flux at long time
            newFluxes[key] = self.lastTurb[key] ** 2 / self.lastDrive[key]

        return newFluxes
