# Configuration

Configuring the integration involves two sides: the **Gundi portal** (this connector's settings) and the **Garmin Explore Professional portal** (IPC setup).

## Gundi portal configuration

The connector exposes three configuration surfaces, rendered as forms in the Gundi portal.

### Authentication (`auth` action)

Required for sending messages to devices (IPC Inbound). Defined by `AuthenticateConfig` in `app/actions/configurations.py`:

| Field | Description |
|-------|-------------|
| `api_url` | Base URL for the inReach IPC Inbound API. Defaults to Garmin's production endpoint (`https://explore.garmin.com`) if not overridden. |
| `username` | Username for the inReach Professional account's IPC Inbound credentials |
| `password` | Password (stored as a secret, rendered as a password field) |

The portal's **Test** button executes the `auth` action, which validates the credentials against Garmin's Pingback endpoint before saving.

!!! tip "Outbound-only integrations"
    All three fields are optional at the schema level so that integrations used only as data providers (device → EarthRanger) can be configured without IPC Inbound credentials. Message push will fail without them.

### Webhook (`InReachWebhookConfig`)

Controls what the connector extracts from IPC Outbound events (`app/webhooks/configurations.py`):

| Field | Default | Description |
|-------|---------|-------------|
| `include_messages` | `true` | Extract free-text events (`messageCode = 3`) as two-way messages |
| `include_observations` | `true` | Extract every event as a location observation |

### Push messages (`push_messages` action)

`PushMessageConfig` currently has no settings — enabling the action on the integration is all that is required. It uses the credentials from the `auth` configuration.

## Garmin-side configuration

Performed by the Garmin Professional account administrator in Garmin Explore:

1. **IPC Outbound**: configure the outbound URL to point at this connector's webhook endpoint. Gundi provides the URL (including the integration's API key) when the integration is created — it routes to `POST /webhooks/` on this service.
2. **IPC Inbound**: obtain IPC Inbound credentials for the Professional account and enter them in the Gundi portal's authentication form.

See [Garmin Accounts & Flex Plans](garmin-accounts.md) for what account type and device service plans are required, and a checklist for verifying that a device can participate in the integration.

## EarthRanger-side notes

- Devices appear in EarthRanger as subjects of type `ranger` with a `gps-radio` source named by the device IMEI, created automatically the first time the device reports through the webhook.
- Two-way messaging uses EarthRanger's messaging feature; outgoing messages are routed through Gundi to the `push_messages` action and addressed by the device IMEI.
