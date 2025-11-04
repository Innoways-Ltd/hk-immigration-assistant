import { MapContainer, TileLayer, Marker, Tooltip, Polyline } from "react-leaflet";
import { useSettlement } from "@/lib/hooks/use-settlement";
import { useEffect, useState, useRef } from "react";
import { Map, divIcon } from "leaflet";
import { cn } from "@/lib/utils";
import { SettlementCard } from "@/components/SettlementCard";
import { PlaceCard } from "@/components/PlaceCard";
import { useMediaQuery } from "@/lib/hooks/use-media-query";

export type MapCanvasProps = {
  className?: string;
}

export function MapCanvas({ className }: MapCanvasProps) {
  const [map, setMap] = useState<Map | null>(null);
  const { settlementPlan } = useSettlement();
  const isDesktop = useMediaQuery("(min-width: 900px)");

  // Auto-focus map on settlement plan center
  useEffect(() => {
    if (map && settlementPlan) {
      map.setView(
        [settlementPlan.center_latitude, settlementPlan.center_longitude],
        settlementPlan.zoom || 14,
        { animate: true }
      );
    }
  }, [map, settlementPlan]);

  return (
		<div className="">
			<MapContainer
				className={cn("w-screen h-screen", className)}
				style={{ zIndex: 0 }}
				center={[0, 0]}
				zoom={1}
				zoomAnimationThreshold={100}
				zoomControl={false}
				ref={setMap}
			>
				<TileLayer
					url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
					attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
				/>
      {settlementPlan && settlementPlan.service_locations && (
        <>
          {/* Draw path connecting service locations */}
          {settlementPlan.service_locations.length > 1 && (
            <Polyline
              positions={settlementPlan.service_locations.map(loc => [loc.latitude, loc.longitude])}
              color="#3b82f6"
              weight={3}
              opacity={0.6}
              dashArray="10, 10"
            />
          )}
          {/* Markers for service locations */}
          {settlementPlan.service_locations.map((place, i) => (
            <Marker 
              key={i} 
              position={[place.latitude, place.longitude]}
              icon={divIcon({
                className: "bg-transparent",
                html: `<div class="bg-blue-500 text-white w-8 h-8 rounded-full flex items-center justify-center font-bold border-2 border-white shadow-lg">${i + 1}</div>`,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
              })}
            >
              <Tooltip offset={[10, 0]} opacity={1}>
                <PlaceCard shouldShowCheckbox={false} className="border-none overflow-y-auto shadow-none" place={place} />
              </Tooltip>
            </Marker>
          ))}
        </>
      )}
      </MapContainer>
      {map && isDesktop && (
        <div className="absolute h-screen top-0 left-0 p-6 pointer-events-none flex items-start w-[35%] md:w-[40%] lg:w-[35%] 2xl:w-[30%]">
          <SettlementCard className="w-full h-full pointer-events-auto" />
        </div>
      )}
			</div>
  );
}