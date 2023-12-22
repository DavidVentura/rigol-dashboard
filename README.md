# Rigol DS1054Z Dashboard

This is a proof of concept for exposing the samples from my oscilloscope into a live-updating web-ui.
The UI is 500-600ms delayed when comparing the the scope's screen.

![alt text](https://github.com/DavidVentura/rigol-dashboard/blob/master/artifacts/recording.gif?raw=true)


Capturing the data-points should be done by an external process, onto an external database, but that was too much effort for a PoC.

## Usage

```sh
python3 rigol_dashboard/upd.py 169.254.253.32
```

The dashboard will be accessible on http://0.0.0.0:8050
