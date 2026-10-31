"""Tests for provider-to-frontend response transformations."""

import json
from pathlib import Path

from backend.bus_views import bus_service_view, bus_stop_locations, buses_view
from backend.healthcare import healthcare_view, parse_wait_page
from backend.presenters import (
    cameras_view,
    environment_view,
    nearby_places,
    rail_status_view,
    search_places,
    transport_view,
    weather_alerts_view,
    weather_view,
)


def test_hospital_wait_pages_are_normalized() -> None:
    fixture_dir = Path(__file__).parents[1] / "fixtures" / "providers"
    pages = {
        source: (fixture_dir / filename).read_text(encoding="utf-8")
        for source, filename in {
            "ttsh": "ttsh_emergency.html",
            "woodlands": "woodlands_emergency.html",
            "nuhs": "nuhs_emergency.html",
        }.items()
    }
    sources = {
        source: {"name": source.upper(), "url": f"https://{source}.example"}
        for source in pages
    }

    result = healthcare_view(pages, sources)

    assert len(result["facilities"]) == 5
    ttsh = next(item for item in result["facilities"] if item["cluster"] == "NHG")
    assert ttsh["patients_waiting"] == 3
    assert ttsh["wait_to_doctor_minutes"] == 19
    woodlands = next(
        item for item in result["facilities"] if item["hospital"] == "Woodlands Health"
    )
    assert woodlands["wait_to_doctor_minutes"] == 8
    nuh_children = next(
        item
        for item in result["facilities"]
        if item["hospital"] == "National University Hospital"
        and item["category"] == "children"
    )
    assert nuh_children["patients_waiting"] == 2
    assert nuh_children["bed_wait_minutes"] == 120


def test_unavailable_hospital_source_is_reported() -> None:
    result = healthcare_view(
        {
            "ttsh": (
                "<p>No. of Patients Awaiting Consultation: 2</p>"
                "<p>Average Consult Wait Time: 10 min</p>"
            )
        },
        {
            "ttsh": {"name": "TTSH", "url": "https://ttsh.example"},
            "nuhs": {"name": "NUHS", "url": "https://nuhs.example"},
        },
        {"nuhs": "provider unavailable"},
    )

    unavailable = next(
        source for source in result["sources"] if source["id"] == "nuhs"
    )
    assert unavailable["state"] == "unavailable"
    assert unavailable["error"] == "provider unavailable"
    assert parse_wait_page("<p>unrelated page</p>", "ttsh") == []


def test_weather_fixture_becomes_typed_sensor_data() -> None:
    fixture = (
        Path(__file__).parents[1]
        / "fixtures"
        / "providers"
        / "data_gov_realtime_weather.json"
    )
    payload = json.loads(fixture.read_text(encoding="utf-8"))

    result = weather_view({"air-temperature": payload})

    assert result["metrics"][0]["value"] == 29.4
    assert result["readings"][0] == {
        "id": "air-temperature-S24",
        "name": "Changi",
        "latitude": 1.3678,
        "longitude": 103.9826,
        "metric": "air-temperature",
        "unit": "°C",
        "value": 29.4,
        "observed_at": "2026-10-30T12:00:00+08:00",
    }


def test_search_and_nearby_ignore_records_without_coordinates() -> None:
    payload = {
        "results": [
            {
                "SEARCHVAL": "City Hall",
                "ADDRESS": "3 St Andrew's Road",
                "BUILDING": "City Hall",
                "LATITUDE": "1.2932",
                "LONGITUDE": "103.8520",
            },
            {"ADDRESS": "Missing coordinates"},
        ]
    }

    search = search_places(payload)
    nearby = nearby_places(1.29, 103.85, {"mrt-stations": payload})

    assert len(search) == 1
    assert search[0]["label"].startswith("City Hall")
    assert len(nearby["places"]) == 1
    assert nearby["places"][0]["distance_m"] > 0


def test_bus_arrivals_are_grouped_and_load_is_mapped() -> None:
    result = buses_view(
        {
            "Services": [
                {
                    "ServiceNo": "36",
                    "NextBus": {
                        "EstimatedArrival": "2099-10-30T12:00:00+00:00",
                        "DestinationCode": "CG2",
                        "Load": "SEA",
                        "Feature": "WAB",
                        "Type": "DD",
                    },
                    "NextBus2": {},
                    "NextBus3": {
                        "EstimatedArrival": "not-a-time",
                        "Load": "SDA",
                        "Type": "SD",
                    },
                }
            ]
        },
        "01012",
        {
            "01012": {
                "Description": "Opp Blk 123",
                "RoadName": "Admiralty Rd",
                "Latitude": 1.44,
                "Longitude": 103.8,
            },
            "CG2": {"Description": "Changi Airport Ter 2"},
        },
    )

    assert result["stop"]["code"] == "01012"
    assert result["stop"]["name"] == "Opp Blk 123"
    assert result["stop"]["latitude"] == 1.44
    assert result["arrivals"][0]["service_no"] == "36"
    assert result["arrivals"][0]["destination"] == "Changi Airport Ter 2"
    assert result["arrivals"][0]["visits"][0]["load"] == "seats"
    assert result["arrivals"][0]["visits"][0]["wheelchair"] is True
    assert result["arrivals"][0]["visits"][0]["type"] == "DD"
    assert result["arrivals"][0]["visits"][1]["minutes"] is None
    assert result["arrivals"][0]["visits"][2]["minutes"] is None


def test_bus_stop_locations_skip_records_without_coordinates() -> None:
    result = bus_stop_locations(
        {
            "64611": {
                "Description": "Blk 913",
                "RoadName": "Tampines St 91",
                "Latitude": "1.35",
                "Longitude": "103.94",
            },
            "00000": {"Description": "Missing"},
        }
    )

    assert result["stops"] == [
        {
            "code": "64611",
            "name": "Blk 913",
            "road": "Tampines St 91",
            "latitude": 1.35,
            "longitude": 103.94,
        }
    ]


def test_bus_service_view_orders_stops_by_sequence() -> None:
    result = bus_service_view(
        [
            {
                "ServiceNo": "159",
                "Direction": "1",
                "StopSequence": "2",
                "BusStopCode": "64611",
            },
            {
                "ServiceNo": "159",
                "Direction": "1",
                "StopSequence": "1",
                "BusStopCode": "64009",
                "WD_FirstBus": "0530",
                "WD_LastBus": "2330",
            },
        ],
        "159",
        {
            "64009": {
                "Description": "Sengkang Int",
                "Latitude": 1.39,
                "Longitude": 103.89,
            },
            "64611": {
                "Description": "Blk 913",
                "Latitude": 1.35,
                "Longitude": 103.94,
            },
        },
    )

    direction = result["directions"][0]
    assert direction["origin"] == "Sengkang Int"
    assert direction["destination"] == "Blk 913"
    assert direction["first_bus"] == "0530"
    assert [stop["code"] for stop in direction["stops"]] == ["64009", "64611"]


def test_camera_view_preserves_provider_camera_ids() -> None:
    result = cameras_view(
        {
            "items": [
                {
                    "cameras": [
                        {
                            "camera_id": "2701",
                            "timestamp": "2026-10-30T14:00:00+00:00",
                            "image": "https://example.test/causeway.jpg",
                            "location": {
                                "latitude": 1.45,
                                "longitude": 103.77,
                            },
                        }
                    ]
                }
            ]
        }
    )

    assert result["cameras"][0]["id"] == "2701"
    assert result["cameras"][0]["name"] == "Woodlands Causeway (Towards Johor)"
    assert result["cameras"][0]["image_url"].endswith("causeway.jpg")


def test_environment_view_reads_uv_and_wbgt_record_payloads() -> None:
    result = environment_view(
        {
            "psi": {
                "data": {
                    "regionMetadata": [
                        {
                            "name": "central",
                            "labelLocation": {
                                "latitude": 1.35,
                                "longitude": 103.82,
                            },
                        }
                    ],
                    "items": [
                        {
                            "readings": {
                                "psi_twenty_four_hourly": {"central": 55}
                            }
                        }
                    ],
                }
            },
            "uv": {
                "data": {
                    "records": [
                        {
                            "index": [
                                {"hour": "2026-10-30T12:00:00+08:00", "value": 8},
                                {"hour": "2026-10-30T11:00:00+08:00", "value": 4},
                            ]
                        }
                    ]
                }
            },
            "wbgt": {
                "data": {
                    "records": [
                        {
                            "item": {
                                "readings": [
                                    {
                                        "wbgt": "26.2",
                                        "heatStress": "Low",
                                        "station": {
                                            "id": "S104",
                                            "name": "Admiralty",
                                        },
                                        "location": {
                                            "latitude": 1.44,
                                            "longitude": 103.8,
                                        },
                                    },
                                    {"wbgt": "25.8"},
                                ]
                            }
                        }
                    ]
                }
            },
        }
    )

    metrics = {metric["id"]: metric for metric in result["metrics"]}
    assert metrics["psi"]["value"] == 55.0
    assert metrics["uv"]["value"] == 8
    assert metrics["wbgt"]["value"] == 26.0
    assert result["regions"][0]["name"] == "Central"
    assert result["uv_index"] == [
        {"timestamp": "2026-10-30T12:00:00+08:00", "value": 8.0},
        {"timestamp": "2026-10-30T11:00:00+08:00", "value": 4.0},
    ]
    assert result["readings"][0]["name"] == "Admiralty"
    assert result["readings"][0]["metric"] == "wbgt"
    assert result["readings"][0]["detail"] == "Low"


def test_weather_alerts_and_rail_status_are_normalized() -> None:
    alerts = weather_alerts_view(
        {
            "lightning": {
                "data": {
                    "records": [
                        {
                            "datetime": "2026-10-30T12:00:00+08:00",
                            "item": {
                                "readings": [
                                    {
                                        "text": "Lightning detected",
                                        "type": "C",
                                        "location": {
                                            "latitude": 1.35,
                                            "longitude": 103.82,
                                        },
                                    }
                                ]
                            },
                        }
                    ]
                }
            },
            "flood": {
                "data": {
                    "records": [
                        {
                            "datetime": "2026-10-30T12:01:00+08:00",
                            "item": {
                                "readings": [
                                    {
                                        "description": "Flooding reported",
                                        "instruction": "Avoid the area",
                                    }
                                ]
                            },
                        }
                    ]
                }
            },
        }
    )

    assert [alert["severity"] for alert in alerts] == ["warning", "critical"]
    assert alerts[1]["detail"] == "Avoid the area"
    assert alerts[0]["latitude"] == 1.35
    assert alerts[0]["longitude"] == 103.82
    rail_status = rail_status_view(
        {
            "value": {
                "Status": 1,
                "Message": [{"Content": "Unrelated bus advisory"}],
            }
        }
    )
    assert rail_status["state"] == "normal"
    assert "detail" not in rail_status
    assert rail_status_view({"value": {"Status": 0}})["state"] == "disrupted"


def test_transport_view_includes_toggleable_road_map_layers() -> None:
    result = transport_view(
        {
            "taxis": {
                "features": [
                    {
                        "properties": {"taxi_count": 123},
                        "geometry": {"coordinates": ["103.8 1.3"]},
                    }
                ]
            },
            "cameras": {
                "items": [
                    {
                        "cameras": [
                            {
                                "camera_id": "2701",
                                "location": {
                                    "latitude": 1.45,
                                    "longitude": 103.77,
                                },
                            }
                        ]
                    }
                ]
            },
            "incidents": {
                "value": [
                    {
                        "Type": "Accident",
                        "Latitude": 1.31,
                        "Longitude": 103.81,
                    }
                ]
            },
            "vms": {
                "value": [
                    {
                        "Latitude": 1.32,
                        "Longitude": 103.82,
                        "Message": "Slow traffic",
                    }
                ]
            },
        }
    )

    assert result["metrics"][0]["value"] == 123
    assert {point["category"] for point in result["points"]} == {
        "taxi",
        "camera",
        "incident",
        "vms",
    }
