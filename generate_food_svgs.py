import os
import xml.etree.ElementTree as ET

def generate_all_svgs():
    svgs = {}

    # Common defs / helper
    def make_svg(key, bg_start, bg_end, is_veg, title, subtitle, food_art):
        badge_veg = """
        <rect x="358" y="14" width="26" height="26" rx="6" fill="#ffffff" stroke="#16a34a" stroke-width="2" />
        <circle cx="371" cy="27" r="6" fill="#16a34a" />
        """
        badge_nonveg = """
        <rect x="358" y="14" width="26" height="26" rx="6" fill="#ffffff" stroke="#dc2626" stroke-width="2" />
        <polygon points="371,20 378,32 364,32" fill="#dc2626" />
        """
        badge = badge_veg if is_veg else badge_nonveg

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 250" width="100%" height="100%">
  <defs>
    <linearGradient id="bg-{key}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_start}" />
      <stop offset="100%" stop-color="{bg_end}" />
    </linearGradient>
    <radialGradient id="glow-{key}" cx="50%" cy="45%" r="60%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.6" />
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0" />
    </radialGradient>
    <filter id="shadow-{key}" x="-10%" y="-10%" width="120%" height="130%">
      <feDropShadow dx="0" dy="6" stdDeviation="8" flood-color="#0f172a" flood-opacity="0.12" />
    </filter>
    <filter id="pill-shadow" x="-5%" y="-10%" width="110%" height="130%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#0f172a" flood-opacity="0.08" />
    </filter>
  </defs>

  <!-- Background Canvas -->
  <rect width="100%" height="100%" fill="url(#bg-{key})" rx="16" />
  <rect width="100%" height="100%" fill="url(#glow-{key})" rx="16" />

  <!-- Diet Badge -->
  {badge}

  <!-- Food Art Centerpiece -->
  <g id="food-art" filter="url(#shadow-{key})">
    {food_art}
  </g>

  <!-- Title Pill -->
  <g id="label-pill" filter="url(#pill-shadow)">
    <rect x="65" y="194" width="270" height="42" rx="21" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.2" />
    <text x="200" y="212" font-size="13" font-weight="700" fill="#0f172a" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">{title}</text>
    <text x="200" y="226" font-size="9.5" font-weight="500" fill="#64748b" text-anchor="middle" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif">{subtitle}</text>
  </g>
</svg>"""

    # 1. Dum Biryani
    svgs["biryani"] = make_svg(
        "biryani", "#fff7ed", "#fed7aa", False, "Dum Biryani", "Fragrant Saffron Basmati Feast",
        """
        <!-- Handi Pot Shadow & Base -->
        <ellipse cx="200" cy="168" rx="82" ry="18" fill="rgba(15,23,42,0.18)" />
        <path d="M125 105 C 120 155, 150 170, 200 170 C 250 170, 280 155, 275 105 Z" fill="#9a3412" />
        <ellipse cx="200" cy="105" rx="75" ry="24" fill="#c2410c" />
        <ellipse cx="200" cy="105" rx="70" ry="20" fill="#7c2d12" />
        <!-- Rice Mound -->
        <ellipse cx="200" cy="100" rx="66" ry="24" fill="#fef3c7" />
        <path d="M136 100 Q 200 68 264 100 Q 200 95 136 100 Z" fill="#facc15" opacity="0.9" />
        <!-- Saffron & Spiced Rice Details -->
        <circle cx="175" cy="90" r="4" fill="#ea580c" />
        <circle cx="215" cy="85" r="5" fill="#f59e0b" />
        <circle cx="190" cy="100" r="4.5" fill="#ca8a04" />
        <circle cx="230" cy="98" r="3.5" fill="#ea580c" />
        <!-- Boiled Egg Half -->
        <ellipse cx="165" cy="94" rx="14" ry="10" fill="#ffffff" transform="rotate(-15 165 94)" />
        <circle cx="165" cy="94" r="6" fill="#f59e0b" />
        <!-- Caramelized Onions & Mint -->
        <path d="M185 82 Q 192 78 198 84" stroke="#78350f" stroke-width="2.5" stroke-linecap="round" fill="none" />
        <path d="M210 92 Q 220 88 226 94" stroke="#78350f" stroke-width="2.5" stroke-linecap="round" fill="none" />
        <path d="M180 102 C 180 97, 188 97, 188 102 C 188 107, 180 107, 180 102 Z" fill="#16a34a" />
        <path d="M220 103 C 220 98, 227 98, 227 103 C 227 108, 220 108, 220 103 Z" fill="#16a34a" />
        <!-- Steam -->
        <path d="M192 65 Q 186 50 193 36" stroke="rgba(245,158,11,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M208 62 Q 215 48 208 34" stroke="rgba(245,158,11,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        """
    )

    # 2. Dal & Steamed Rice
    svgs["dal_rice"] = make_svg(
        "dal_rice", "#fefce8", "#fef08a", True, "Dal &amp; Steamed Rice", "Yellow Tadka Dal &amp; Fluffy Rice",
        """
        <!-- Thali Platter -->
        <ellipse cx="200" cy="170" rx="86" ry="18" fill="rgba(15,23,42,0.15)" />
        <ellipse cx="200" cy="115" rx="84" ry="52" fill="#cbd5e1" />
        <ellipse cx="200" cy="115" rx="80" ry="48" fill="#e2e8f0" />
        <ellipse cx="200" cy="115" rx="76" ry="44" fill="#f8fafc" />
        <!-- Steamed Rice Mound (Left) -->
        <ellipse cx="165" cy="118" rx="42" ry="32" fill="#ffffff" />
        <path d="M125 118 Q 165 88 205 118 Q 165 112 125 118 Z" fill="#f1f5f9" />
        <!-- Melting Ghee on Rice -->
        <ellipse cx="165" cy="108" rx="10" ry="6" fill="#facc15" />
        <circle cx="165" cy="108" r="4" fill="#eab308" />
        <!-- Dal Katori (Right) -->
        <ellipse cx="232" cy="116" rx="34" ry="26" fill="#94a3b8" />
        <ellipse cx="232" cy="115" rx="31" ry="23" fill="#fbbf24" />
        <ellipse cx="232" cy="115" rx="27" ry="19" fill="#f59e0b" />
        <!-- Dal Tadka Spices & Coriander -->
        <circle cx="225" cy="112" r="2" fill="#1e293b" />
        <circle cx="236" cy="118" r="1.8" fill="#1e293b" />
        <circle cx="242" cy="110" r="1.8" fill="#1e293b" />
        <path d="M228 108 Q 235 104 238 111" stroke="#dc2626" stroke-width="2.2" stroke-linecap="round" fill="none" />
        <path d="M224 116 C 224 112, 230 112, 230 116 C 230 120, 224 120, 224 116 Z" fill="#15803d" />
        <!-- Steam -->
        <path d="M165 80 Q 160 66 166 52" stroke="rgba(203,213,225,0.7)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        <path d="M232 84 Q 238 70 232 56" stroke="rgba(245,158,11,0.6)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 3. Roti & Sabzi Thali
    svgs["roti_curry"] = make_svg(
        "roti_curry", "#fff7ed", "#ffedd5", True, "Roti &amp; Sabzi Thali", "Golden Whole Wheat Rotis &amp; Curry",
        """
        <ellipse cx="200" cy="170" rx="86" ry="18" fill="rgba(15,23,42,0.15)" />
        <ellipse cx="200" cy="115" rx="84" ry="52" fill="#d1d5db" />
        <ellipse cx="200" cy="115" rx="76" ry="44" fill="#f3f4f6" />
        <!-- Stack of 3 Rotis (Left) -->
        <ellipse cx="152" cy="126" rx="36" ry="24" fill="#fed7aa" stroke="#ea580c" stroke-width="1" />
        <circle cx="145" cy="122" r="2" fill="#c2410c" />
        <circle cx="160" cy="128" r="2.5" fill="#9a3412" />
        <ellipse cx="155" cy="118" rx="35" ry="23" fill="#ffedd5" stroke="#ea580c" stroke-width="1" />
        <circle cx="148" cy="115" r="2" fill="#c2410c" />
        <circle cx="164" cy="120" r="2.2" fill="#9a3412" />
        <ellipse cx="158" cy="110" rx="34" ry="22" fill="#fef3c7" stroke="#ea580c" stroke-width="1.2" />
        <circle cx="150" cy="106" r="2.2" fill="#c2410c" />
        <circle cx="168" cy="112" r="2" fill="#9a3412" />
        <circle cx="160" cy="108" r="1.8" fill="#c2410c" />
        <!-- Sabzi Bowl (Right) -->
        <ellipse cx="236" cy="116" rx="36" ry="26" fill="#9ca3af" />
        <ellipse cx="236" cy="115" rx="33" ry="23" fill="#ea580c" />
        <!-- Veggies in Sabzi -->
        <circle cx="226" cy="110" r="5" fill="#22c55e" />
        <circle cx="244" cy="118" r="4.5" fill="#22c55e" />
        <rect x="230" y="112" width="7" height="7" rx="2" fill="#fde047" />
        <rect x="240" y="106" width="6" height="6" rx="1.5" fill="#f97316" />
        <path d="M233 120 C 233 115, 240 115, 240 120 C 240 125, 233 125, 233 120 Z" fill="#15803d" />
        <!-- Steam -->
        <path d="M236 84 Q 242 70 236 56" stroke="rgba(234,88,12,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 4. Moong Dal Khichdi
    svgs["khichdi"] = make_svg(
        "khichdi", "#f0fdf4", "#fef9c3", True, "Moong Dal Khichdi", "Comforting Warm Lentil &amp; Rice Pot",
        """
        <!-- Terracotta Clay Bowl -->
        <ellipse cx="200" cy="168" rx="80" ry="18" fill="rgba(15,23,42,0.16)" />
        <path d="M130 110 C 130 162, 160 172, 200 172 C 240 172, 270 162, 270 110 Z" fill="#b45309" />
        <ellipse cx="200" cy="110" rx="70" ry="28" fill="#d97706" />
        <ellipse cx="200" cy="110" rx="64" ry="24" fill="#92400e" />
        <!-- Creamy Khichdi -->
        <ellipse cx="200" cy="108" rx="60" ry="21" fill="#eab308" />
        <ellipse cx="200" cy="108" rx="52" ry="17" fill="#facc15" />
        <!-- Melting Desi Ghee Cube & Pool -->
        <ellipse cx="200" cy="107" rx="18" ry="9" fill="#fef08a" />
        <rect x="194" y="102" width="12" height="9" rx="2" fill="#fde047" stroke="#eab308" stroke-width="1" />
        <!-- Roasted Cumin Seeds -->
        <line x1="172" y1="104" x2="176" y2="108" stroke="#451a03" stroke-width="2" stroke-linecap="round" />
        <line x1="222" y1="106" x2="226" y2="110" stroke="#451a03" stroke-width="2" stroke-linecap="round" />
        <line x1="184" y1="114" x2="188" y2="112" stroke="#451a03" stroke-width="2" stroke-linecap="round" />
        <!-- Papad Triangle -->
        <polygon points="144,98 126,72 152,86" fill="#fef08a" stroke="#ca8a04" stroke-width="1.2" />
        <circle cx="138" cy="84" r="1.5" fill="#92400e" />
        <circle cx="144" cy="90" r="1.5" fill="#92400e" />
        <!-- Soothing Steam -->
        <path d="M192 68 Q 186 52 192 38" stroke="rgba(234,179,8,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M208 65 Q 214 49 208 35" stroke="rgba(234,179,8,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        """
    )

    # 5. Vegetable Fried Rice
    svgs["fried_rice"] = make_svg(
        "fried_rice", "#fefce8", "#ffedd5", True, "Vegetable Fried Rice", "Wok-Tossed Garden Vegetables &amp; Rice",
        """
        <!-- Wok Bowl -->
        <ellipse cx="200" cy="168" rx="82" ry="18" fill="rgba(15,23,42,0.18)" />
        <path d="M128 108 C 128 160, 160 170, 200 170 C 240 170, 272 160, 272 108 Z" fill="#1e293b" />
        <ellipse cx="200" cy="108" rx="72" ry="26" fill="#334155" />
        <ellipse cx="200" cy="107" rx="66" ry="22" fill="#fef3c7" />
        <!-- Wok Grains & Colored Diced Veg -->
        <ellipse cx="200" cy="105" rx="58" ry="18" fill="#fde68a" />
        <rect x="170" y="100" width="5" height="5" rx="1" fill="#f97316" />
        <rect x="210" y="98" width="5" height="5" rx="1" fill="#f97316" />
        <rect x="190" y="110" width="5.5" height="5.5" rx="1" fill="#f97316" />
        <circle cx="160" cy="106" r="3.5" fill="#22c55e" />
        <circle cx="182" cy="102" r="3.5" fill="#22c55e" />
        <circle cx="225" cy="104" r="3.5" fill="#22c55e" />
        <circle cx="202" cy="112" r="3.5" fill="#22c55e" />
        <circle cx="178" cy="111" r="3" fill="#eab308" />
        <circle cx="218" cy="110" r="3" fill="#eab308" />
        <!-- Spring Onion Slices -->
        <rect x="195" y="99" width="7" height="3" rx="1" fill="#15803d" transform="rotate(25 195 99)" />
        <rect x="170" y="108" width="7" height="3" rx="1" fill="#15803d" transform="rotate(-20 170 108)" />
        <!-- Chopsticks resting across rim -->
        <line x1="140" y1="80" x2="250" y2="128" stroke="#78350f" stroke-width="4" stroke-linecap="round" />
        <line x1="145" y1="74" x2="255" y2="122" stroke="#92400e" stroke-width="3" stroke-linecap="round" />
        """
    )

    # 6. Paneer Masala & Roti
    svgs["paneer_curry"] = make_svg(
        "paneer_curry", "#fff1f2", "#ffe4e6", True, "Paneer Masala &amp; Roti", "Cottage Cheese Cubes in Makhani Gravy",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.16)" />
        <!-- Copper Balti / Handi -->
        <path d="M136 106 C 136 160, 164 170, 200 170 C 236 170, 264 160, 264 106 Z" fill="#b45309" />
        <ellipse cx="200" cy="106" rx="64" ry="24" fill="#d97706" />
        <!-- Gravy -->
        <ellipse cx="200" cy="105" rx="58" ry="20" fill="#dc2626" />
        <ellipse cx="200" cy="105" rx="52" ry="17" fill="#ea580c" />
        <!-- Paneer Cubes -->
        <rect x="168" y="96" width="16" height="13" rx="2" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <rect x="198" y="93" width="18" height="14" rx="2" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <rect x="180" y="104" width="16" height="13" rx="2" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <rect x="212" y="102" width="15" height="12" rx="2" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <!-- Cream Swirl -->
        <path d="M175 106 Q 200 114 220 102" stroke="#ffffff" stroke-width="3" stroke-linecap="round" fill="none" opacity="0.9" />
        <!-- Green Chili & Coriander -->
        <path d="M192 98 Q 202 94 206 100" stroke="#16a34a" stroke-width="3" stroke-linecap="round" fill="none" />
        <circle cx="188" cy="104" r="2" fill="#15803d" />
        <circle cx="206" cy="106" r="2" fill="#15803d" />
        <!-- Folded Roti on Side -->
        <polygon points="120,120 150,96 142,130" fill="#fef3c7" stroke="#d97706" stroke-width="1.2" />
        <circle cx="134" cy="115" r="1.5" fill="#9a3412" />
        <!-- Steam -->
        <path d="M200 70 Q 206 54 200 40" stroke="rgba(234,88,12,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 7. Idli & Sambar
    svgs["idli_sambar"] = make_svg(
        "idli_sambar", "#ecfdf5", "#d1fae5", True, "Idli &amp; Sambar", "Steamed Fluffy Idlis, Sambar &amp; Chutney",
        """
        <ellipse cx="200" cy="170" rx="86" ry="18" fill="rgba(15,23,42,0.15)" />
        <!-- Banana Leaf Base -->
        <ellipse cx="200" cy="118" rx="85" ry="48" fill="#15803d" />
        <ellipse cx="200" cy="118" rx="81" ry="44" fill="#16a34a" />
        <line x1="120" y1="118" x2="280" y2="118" stroke="#15803d" stroke-width="2" opacity="0.6" />
        <!-- 3 Steamed Soft Idlis -->
        <ellipse cx="154" cy="122" rx="26" ry="18" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1" />
        <ellipse cx="178" cy="106" rx="26" ry="18" fill="#ffffff" stroke="#e2e8f0" stroke-width="1.2" />
        <ellipse cx="198" cy="124" rx="26" ry="18" fill="#f8fafc" stroke="#e2e8f0" stroke-width="1" />
        <!-- Sambar Katori (Top Right) -->
        <ellipse cx="242" cy="106" rx="26" ry="19" fill="#94a3b8" />
        <ellipse cx="242" cy="105" rx="23" ry="16" fill="#ea580c" />
        <circle cx="238" cy="104" r="3.5" fill="#ca8a04" />
        <circle cx="246" cy="108" r="2" fill="#1e293b" />
        <path d="M240 102 C 240 99, 244 99, 244 102 Z" fill="#15803d" />
        <!-- Coconut Chutney Katori (Bottom Right) -->
        <ellipse cx="236" cy="135" rx="22" ry="16" fill="#94a3b8" />
        <ellipse cx="236" cy="134" rx="19" ry="13" fill="#ffffff" />
        <!-- Mustard seeds & Curry Leaf in Chutney -->
        <circle cx="232" cy="133" r="1.5" fill="#1e293b" />
        <circle cx="240" cy="136" r="1.5" fill="#1e293b" />
        <circle cx="236" cy="132" r="1.2" fill="#1e293b" />
        <path d="M234 135 C 234 132, 238 132, 238 135 Z" fill="#16a34a" />
        """
    )

    # 8. Crispy Dosa Platter
    svgs["dosa_pack"] = make_svg(
        "dosa_pack", "#fffbeb", "#fef3c7", True, "Crispy Dosa Platter", "Golden Rolled Crepe, Sambar &amp; Chutneys",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.15)" />
        <!-- Platter -->
        <ellipse cx="200" cy="118" rx="86" ry="48" fill="#e2e8f0" />
        <ellipse cx="200" cy="118" rx="82" ry="44" fill="#f8fafc" />
        <!-- Golden Rolled Dosa -->
        <path d="M125 125 C 130 105, 230 85, 265 105 C 270 120, 240 135, 145 138 Z" fill="#d97706" />
        <path d="M130 123 C 135 108, 225 90, 258 107 C 248 116, 175 128, 142 129 Z" fill="#f59e0b" />
        <!-- Dosa porous roasted brown marks -->
        <line x1="165" y1="112" x2="175" y2="114" stroke="#92400e" stroke-width="2" stroke-linecap="round" />
        <line x1="190" y1="108" x2="202" y2="111" stroke="#92400e" stroke-width="2.5" stroke-linecap="round" />
        <line x1="220" y1="105" x2="232" y2="108" stroke="#92400e" stroke-width="2" stroke-linecap="round" />
        <!-- 3 Dip Bowls (Front) -->
        <!-- Sambar -->
        <ellipse cx="152" cy="138" rx="18" ry="12" fill="#94a3b8" />
        <ellipse cx="152" cy="137" rx="15" ry="10" fill="#ea580c" />
        <!-- Coconut Chutney -->
        <ellipse cx="195" cy="142" rx="18" ry="12" fill="#94a3b8" />
        <ellipse cx="195" cy="141" rx="15" ry="10" fill="#ffffff" />
        <circle cx="195" cy="140" r="1.5" fill="#1e293b" />
        <!-- Tomato Chutney -->
        <ellipse cx="238" cy="138" rx="18" ry="12" fill="#94a3b8" />
        <ellipse cx="238" cy="137" rx="15" ry="10" fill="#dc2626" />
        """
    )

    # 9. Vegetable Pulao
    svgs["veg_pulao"] = make_svg(
        "veg_pulao", "#fffbeb", "#fef9c3", True, "Vegetable Pulao", "Aromatic Spiced Long-Grain Basmati &amp; Veggies",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="115" rx="82" ry="50" fill="#cbd5e1" />
        <ellipse cx="200" cy="115" rx="76" ry="44" fill="#ffffff" />
        <!-- Pulao Rice Dome -->
        <ellipse cx="200" cy="114" rx="66" ry="36" fill="#fef3c7" />
        <ellipse cx="200" cy="110" rx="54" ry="26" fill="#fef08a" />
        <!-- Whole Spices: Star Anise & Cinnamon -->
        <circle cx="178" cy="98" r="4.5" fill="#451a03" />
        <rect x="215" y="96" width="16" height="4" rx="2" fill="#78350f" transform="rotate(20 215 96)" />
        <!-- Green Peas, Carrots, Golden Cashews -->
        <circle cx="165" cy="112" r="4" fill="#16a34a" />
        <circle cx="192" cy="104" r="4" fill="#16a34a" />
        <circle cx="226" cy="114" r="4" fill="#16a34a" />
        <rect x="180" y="112" width="6" height="6" rx="1.5" fill="#ea580c" />
        <rect x="210" y="108" width="6" height="6" rx="1.5" fill="#ea580c" />
        <!-- Fried Cashew -->
        <path d="M196 118 C 196 114, 204 114, 204 118 C 204 122, 196 122, 196 118 Z" fill="#f59e0b" />
        <!-- Steam -->
        <path d="M200 72 Q 194 58 200 44" stroke="rgba(245,158,11,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 10. Chole & Bhature
    svgs["chole_bhature"] = make_svg(
        "chole_bhature", "#fff7ed", "#fed7aa", True, "Chole &amp; Bhature", "Spicy Amritsari Chole &amp; Puffed Bhature",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.16)" />
        <!-- 2 Large Puffed Bhature (Left & Center) -->
        <ellipse cx="152" cy="116" rx="36" ry="28" fill="#f59e0b" stroke="#d97706" stroke-width="1.5" />
        <ellipse cx="152" cy="114" rx="32" ry="24" fill="#fbbf24" />
        <ellipse cx="186" cy="124" rx="34" ry="26" fill="#f59e0b" stroke="#d97706" stroke-width="1.5" />
        <ellipse cx="186" cy="122" rx="30" ry="22" fill="#fbbf24" />
        <!-- Chole Bowl (Right) -->
        <ellipse cx="240" cy="115" rx="34" ry="26" fill="#9ca3af" />
        <ellipse cx="240" cy="114" rx="30" ry="22" fill="#78350f" />
        <!-- Chickpeas & Garnishes -->
        <circle cx="232" cy="110" r="4.5" fill="#b45309" />
        <circle cx="244" cy="112" r="4.5" fill="#b45309" />
        <circle cx="236" cy="118" r="4.5" fill="#92400e" />
        <circle cx="248" cy="120" r="4" fill="#b45309" />
        <!-- Onion Ring & Lemon Wedge -->
        <circle cx="236" cy="108" r="5" fill="none" stroke="#e879f9" stroke-width="1.8" />
        <path d="M250 106 L 258 108 L 254 114 Z" fill="#facc15" stroke="#ca8a04" stroke-width="1" />
        <!-- Steam -->
        <path d="M240 82 Q 246 68 240 54" stroke="rgba(180,83,9,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 11. Rajma Chawal
    svgs["rajma_chawal"] = make_svg(
        "rajma_chawal", "#fff1f2", "#fee2e2", True, "Rajma Chawal", "North Indian Kidney Bean Curry &amp; Rice",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="115" rx="82" ry="50" fill="#cbd5e1" />
        <ellipse cx="200" cy="115" rx="76" ry="44" fill="#ffffff" />
        <!-- Steamed White Rice (Left Half) -->
        <path d="M128 115 C 128 90, 195 90, 200 115 C 200 140, 128 140, 128 115 Z" fill="#f8fafc" />
        <ellipse cx="160" cy="114" rx="30" ry="22" fill="#ffffff" />
        <!-- Red Rajma Curry (Right Half) -->
        <path d="M200 115 C 200 90, 268 90, 272 115 C 272 140, 200 140, 200 115 Z" fill="#991b1b" />
        <ellipse cx="236" cy="114" rx="32" ry="22" fill="#7f1d1d" />
        <!-- Kidney Beans -->
        <ellipse cx="225" cy="108" rx="5" ry="3.5" fill="#b91c1c" transform="rotate(-20 225 108)" />
        <ellipse cx="242" cy="112" rx="5" ry="3.5" fill="#b91c1c" transform="rotate(30 242 112)" />
        <ellipse cx="230" cy="120" rx="5" ry="3.5" fill="#b91c1c" transform="rotate(10 230 120)" />
        <ellipse cx="248" cy="122" rx="4.5" ry="3" fill="#b91c1c" transform="rotate(-35 248 122)" />
        <!-- Onion rings & green chili in center -->
        <circle cx="196" cy="110" r="6" fill="none" stroke="#d8b4fe" stroke-width="1.8" />
        <path d="M192 118 Q 200 112 208 119" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" fill="none" />
        <!-- Steam -->
        <path d="M236 82 Q 242 68 236 54" stroke="rgba(185,28,28,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 12. Vegetable Hakka Noodles
    svgs["hakka_noodles"] = make_svg(
        "hakka_noodles", "#fff7ed", "#fecdd3", True, "Vegetable Hakka Noodles", "Wok Stir-Fried Noodles &amp; Crisp Veggies",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.18)" />
        <!-- Deep Bowl -->
        <path d="M130 110 C 130 162, 160 172, 200 172 C 240 172, 270 162, 270 110 Z" fill="#991b1b" />
        <ellipse cx="200" cy="110" rx="70" ry="26" fill="#b91c1c" />
        <!-- Golden Tangle of Noodles -->
        <ellipse cx="200" cy="108" rx="64" ry="21" fill="#fef08a" />
        <path d="M148 108 Q 165 96 182 108 Q 200 120 218 108 Q 235 96 252 108" stroke="#ca8a04" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M152 114 Q 172 124 192 112 Q 212 102 232 116 Q 245 120 248 112" stroke="#eab308" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M160 102 Q 180 92 200 104 Q 220 116 240 100" stroke="#facc15" stroke-width="2.5" stroke-linecap="round" fill="none" />
        <!-- Shredded Cabbage, Carrots, Bell Peppers -->
        <line x1="168" y1="104" x2="178" y2="108" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" />
        <line x1="216" y1="102" x2="228" y2="105" stroke="#dc2626" stroke-width="2.5" stroke-linecap="round" />
        <line x1="184" y1="114" x2="194" y2="116" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" />
        <line x1="222" y1="112" x2="232" y2="116" stroke="#16a34a" stroke-width="2.5" stroke-linecap="round" />
        <line x1="190" y1="102" x2="198" y2="106" stroke="#9333ea" stroke-width="2.2" stroke-linecap="round" />
        <!-- Chopsticks Lift -->
        <line x1="135" y1="75" x2="245" y2="120" stroke="#78350f" stroke-width="3.5" stroke-linecap="round" />
        <line x1="140" y1="68" x2="250" y2="114" stroke="#92400e" stroke-width="3" stroke-linecap="round" />
        """
    )

    # 13. Pav Bhaji
    svgs["pav_bhaji"] = make_svg(
        "pav_bhaji", "#fff7ed", "#fed7aa", True, "Pav Bhaji", "Spiced Mashed Vegetable Bhaji &amp; Butter Pav",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="118" rx="86" ry="48" fill="#e2e8f0" />
        <ellipse cx="200" cy="118" rx="82" ry="44" fill="#f8fafc" />
        <!-- 2 Toasted Golden Pav Buns (Left) -->
        <rect x="130" y="98" width="30" height="26" rx="6" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" />
        <rect x="133" y="100" width="24" height="20" rx="4" fill="#fbbf24" />
        <rect x="162" y="98" width="30" height="26" rx="6" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" />
        <rect x="165" y="100" width="24" height="20" rx="4" fill="#fbbf24" />
        <!-- Butter Glaze on Pav -->
        <ellipse cx="145" cy="106" rx="6" ry="3" fill="#fef08a" />
        <ellipse cx="177" cy="106" rx="6" ry="3" fill="#fef08a" />
        <!-- Spicy Bhaji Pool (Right) -->
        <ellipse cx="230" cy="116" rx="38" ry="26" fill="#ea580c" />
        <ellipse cx="230" cy="115" rx="34" ry="22" fill="#c2410c" />
        <!-- Butter Cube Melting in Center of Bhaji -->
        <rect x="222" y="108" width="14" height="10" rx="2" fill="#fef08a" stroke="#facc15" stroke-width="1" />
        <!-- Chopped Onions, Coriander, Lemon -->
        <circle cx="214" cy="118" r="2.2" fill="#a855f7" />
        <circle cx="242" cy="112" r="2.2" fill="#a855f7" />
        <circle cx="238" cy="122" r="2" fill="#15803d" />
        <path d="M254 122 L 262 120 L 258 128 Z" fill="#facc15" stroke="#ca8a04" stroke-width="1" />
        <!-- Steam -->
        <path d="M230 84 Q 236 70 230 56" stroke="rgba(234,88,12,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 14. South Indian Sambar Rice
    svgs["sambar_rice"] = make_svg(
        "sambar_rice", "#fffbeb", "#fef08a", True, "South Indian Sambar Rice", "Tamarind &amp; Lentil Infused Rice Pot",
        """
        <ellipse cx="200" cy="168" rx="80" ry="18" fill="rgba(15,23,42,0.16)" />
        <path d="M132 110 C 132 162, 160 172, 200 172 C 240 172, 268 162, 268 110 Z" fill="#78350f" />
        <ellipse cx="200" cy="110" rx="68" ry="26" fill="#92400e" />
        <!-- Sambar Rice -->
        <ellipse cx="200" cy="108" rx="62" ry="21" fill="#d97706" />
        <ellipse cx="200" cy="108" rx="54" ry="17" fill="#ea580c" />
        <!-- Mustard seeds, cashews, curry leaves -->
        <circle cx="178" cy="106" r="1.8" fill="#1e293b" />
        <circle cx="220" cy="104" r="1.8" fill="#1e293b" />
        <circle cx="196" cy="112" r="1.8" fill="#1e293b" />
        <path d="M185 108 C 185 104, 192 104, 192 108 C 192 112, 185 112, 185 108 Z" fill="#fef08a" />
        <path d="M210 110 C 210 106, 218 106, 218 110 C 218 114, 210 114, 210 110 Z" fill="#fef08a" />
        <path d="M198 102 C 198 98, 204 98, 204 102 C 204 106, 198 106, 198 102 Z" fill="#15803d" />
        <!-- Mini Papadum on Rim -->
        <circle cx="150" cy="98" r="15" fill="#fef08a" stroke="#ca8a04" stroke-width="1.2" />
        <circle cx="146" cy="94" r="1.5" fill="#92400e" />
        <circle cx="152" cy="102" r="1.5" fill="#92400e" />
        <!-- Steam -->
        <path d="M200 70 Q 206 54 200 40" stroke="rgba(217,119,6,0.6)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 15. Mixed Vegetable Curry
    svgs["mix_veg_sabzi"] = make_svg(
        "mix_veg_sabzi", "#f0fdf4", "#fef3c7", True, "Mixed Vegetable Curry", "Homestyle Seasonal Veggie Medley",
        """
        <ellipse cx="200" cy="168" rx="82" ry="18" fill="rgba(15,23,42,0.16)" />
        <path d="M132 108 C 132 160, 162 170, 200 170 C 238 170, 268 160, 268 108 Z" fill="#b45309" />
        <ellipse cx="200" cy="108" rx="68" ry="26" fill="#d97706" />
        <!-- Gravy -->
        <ellipse cx="200" cy="106" rx="62" ry="21" fill="#ea580c" />
        <!-- Colorful Vegetable Medley -->
        <!-- Cauliflower Florets -->
        <ellipse cx="170" cy="102" rx="8" ry="6" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <ellipse cx="218" cy="100" rx="8" ry="6" fill="#ffffff" stroke="#f1f5f9" stroke-width="1" />
        <!-- Green Beans & Peas -->
        <line x1="184" y1="104" x2="198" y2="100" stroke="#16a34a" stroke-width="3" stroke-linecap="round" />
        <circle cx="160" cy="112" r="4" fill="#22c55e" />
        <circle cx="202" cy="114" r="4" fill="#22c55e" />
        <circle cx="232" cy="108" r="4" fill="#22c55e" />
        <!-- Carrots & Potato Cubes -->
        <rect x="180" y="108" width="8" height="8" rx="1.5" fill="#f97316" />
        <rect x="214" y="110" width="8" height="8" rx="1.5" fill="#fde047" />
        <!-- Coriander -->
        <path d="M194 106 C 194 101, 200 101, 200 106 C 200 111, 194 111, 194 106 Z" fill="#15803d" />
        <!-- Steam -->
        <path d="M200 70 Q 194 54 200 40" stroke="rgba(234,88,12,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 16. Poori & Aloo Sabzi
    svgs["poori_bhaji"] = make_svg(
        "poori_bhaji", "#fffbeb", "#fef08a", True, "Poori &amp; Aloo Sabzi", "Puffed Golden Pooris &amp; Spiced Potato Curry",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="118" rx="86" ry="48" fill="#e2e8f0" />
        <ellipse cx="200" cy="118" rx="80" ry="44" fill="#f8fafc" />
        <!-- 3 Puffed Golden Balloon Pooris (Left) -->
        <ellipse cx="146" cy="126" rx="26" ry="20" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" />
        <ellipse cx="146" cy="124" rx="23" ry="17" fill="#fbbf24" />
        <ellipse cx="174" cy="110" rx="28" ry="22" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" />
        <ellipse cx="174" cy="108" rx="25" ry="19" fill="#fbbf24" />
        <ellipse cx="152" cy="104" rx="24" ry="18" fill="#f59e0b" stroke="#d97706" stroke-width="1.2" />
        <ellipse cx="152" cy="102" rx="21" ry="15" fill="#fde047" />
        <!-- Aloo Sabzi Bowl (Right) -->
        <ellipse cx="234" cy="118" rx="34" ry="26" fill="#9ca3af" />
        <ellipse cx="234" cy="117" rx="30" ry="22" fill="#eab308" />
        <!-- Spiced Potato chunks & green chili -->
        <rect x="220" y="112" width="10" height="9" rx="2" fill="#fde047" stroke="#ca8a04" stroke-width="1" />
        <rect x="236" y="116" width="11" height="9" rx="2" fill="#fde047" stroke="#ca8a04" stroke-width="1" />
        <path d="M228 110 Q 236 106 242 112" stroke="#16a34a" stroke-width="2.2" stroke-linecap="round" fill="none" />
        <circle cx="232" cy="122" r="1.8" fill="#15803d" />
        <!-- Steam -->
        <path d="M234 84 Q 240 70 234 56" stroke="rgba(234,179,8,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 17. Samosa & Savory Snacks
    svgs["samosa_snack"] = make_svg(
        "samosa_snack", "#fff7ed", "#fed7aa", True, "Samosa &amp; Savory Snacks", "Crispy Golden Samosas &amp; Tangy Chutneys",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.16)" />
        <!-- Slate Serving Platter -->
        <ellipse cx="200" cy="118" rx="86" ry="46" fill="#334155" />
        <ellipse cx="200" cy="118" rx="82" ry="42" fill="#1e293b" />
        <!-- 2 Golden Triangular Samosas -->
        <!-- Samosa 1 (Left) -->
        <polygon points="160,82 125,135 190,132" fill="#d97706" stroke="#b45309" stroke-width="1.5" />
        <polygon points="160,85 130,132 186,130" fill="#f59e0b" />
        <line x1="160" y1="85" x2="158" y2="131" stroke="#b45309" stroke-width="1.5" opacity="0.7" />
        <!-- Samosa 2 (Right) -->
        <polygon points="215,86 178,136 248,132" fill="#d97706" stroke="#b45309" stroke-width="1.5" />
        <polygon points="215,89 183,133 244,130" fill="#fbbf24" />
        <line x1="215" y1="89" x2="213" y2="131" stroke="#b45309" stroke-width="1.5" opacity="0.7" />
        <!-- Chutney Splashes -->
        <!-- Green Mint Chutney Swirl -->
        <ellipse cx="140" cy="140" rx="14" ry="7" fill="#16a34a" />
        <!-- Tamarind Sweet Chutney Swirl -->
        <ellipse cx="235" cy="138" rx="14" ry="7" fill="#78350f" />
        <!-- Fried Green Chili -->
        <path d="M185 136 Q 198 132 205 138" stroke="#15803d" stroke-width="3" stroke-linecap="round" fill="none" />
        """
    )

    # 18. Club Sandwiches
    svgs["sandwich_meal"] = make_svg(
        "sandwich_meal", "#f0fdf4", "#e0e7ff", True, "Club Sandwiches", "Grilled Multi-Layer Fresh Meal Sandwiches",
        """
        <ellipse cx="200" cy="170" rx="86" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="118" rx="84" ry="46" fill="#cbd5e1" />
        <ellipse cx="200" cy="118" rx="80" ry="42" fill="#ffffff" />
        <!-- Triangular Sandwich 1 (Back) -->
        <polygon points="165,85 125,128 200,126" fill="#fed7aa" stroke="#d97706" stroke-width="1.5" />
        <polygon points="165,88 130,126 195,124" fill="#ffedd5" />
        <!-- Diagonal Grill Marks -->
        <line x1="145" y1="102" x2="175" y2="114" stroke="#78350f" stroke-width="2" stroke-linecap="round" />
        <line x1="155" y1="94" x2="185" y2="106" stroke="#78350f" stroke-width="2" stroke-linecap="round" />
        <!-- Triangular Sandwich 2 (Front) -->
        <polygon points="215,92 170,138 250,134" fill="#fed7aa" stroke="#d97706" stroke-width="1.5" />
        <polygon points="215,95 175,136 245,132" fill="#fef3c7" />
        <!-- Fillings: Lettuce, Tomato, Cheese -->
        <rect x="178" y="128" width="64" height="3" fill="#22c55e" />
        <rect x="180" y="125" width="60" height="3" fill="#ef4444" />
        <rect x="182" y="122" width="56" height="3" fill="#facc15" />
        <!-- Grill Marks -->
        <line x1="192" y1="110" x2="225" y2="124" stroke="#78350f" stroke-width="2" stroke-linecap="round" />
        <line x1="202" y1="102" x2="235" y2="116" stroke="#78350f" stroke-width="2" stroke-linecap="round" />
        <!-- Pick with Olive -->
        <line x1="215" y1="72" x2="215" y2="105" stroke="#ca8a04" stroke-width="2" />
        <circle cx="215" cy="74" r="5" fill="#dc2626" />
        """
    )

    # 19. Assorted Halwa / Mithai
    svgs["sweets_mithai"] = make_svg(
        "sweets_mithai", "#fffbeb", "#fdf2f8", True, "Assorted Halwa &amp; Mithai", "Festive Moong Dal Halwa, Laddoos &amp; Katli",
        """
        <ellipse cx="200" cy="170" rx="88" ry="18" fill="rgba(15,23,42,0.16)" />
        <!-- Silver Festive Thali -->
        <ellipse cx="200" cy="118" rx="86" ry="48" fill="#94a3b8" />
        <ellipse cx="200" cy="118" rx="82" ry="44" fill="#e2e8f0" />
        <ellipse cx="200" cy="118" rx="78" ry="40" fill="#f1f5f9" />
        <!-- Halwa Mound (Center) -->
        <ellipse cx="200" cy="120" rx="36" ry="20" fill="#d97706" />
        <ellipse cx="200" cy="118" rx="30" ry="16" fill="#f59e0b" />
        <!-- Silver Kaju Katli (Left) -->
        <polygon points="152,98 168,110 152,122 136,110" fill="#e2e8f0" stroke="#cbd5e1" stroke-width="1.2" />
        <polygon points="152,100 165,110 152,120 139,110" fill="#ffffff" />
        <!-- Motichoor Laddoos (Right) -->
        <circle cx="242" cy="112" r="14" fill="#ea580c" stroke="#c2410c" stroke-width="1" />
        <circle cx="242" cy="110" r="12" fill="#f97316" />
        <circle cx="236" cy="125" r="12" fill="#ea580c" stroke="#c2410c" stroke-width="1" />
        <circle cx="236" cy="124" r="10" fill="#f97316" />
        <!-- Pistachio & Saffron Garnishes -->
        <circle cx="196" cy="116" r="2" fill="#16a34a" />
        <circle cx="204" cy="118" r="2" fill="#16a34a" />
        <circle cx="198" cy="122" r="2" fill="#16a34a" />
        <line x1="200" y1="112" x2="204" y2="116" stroke="#dc2626" stroke-width="1.5" />
        """
    )

    # 20. Egg Curry & Rice
    svgs["egg_curry_rice"] = make_svg(
        "egg_curry_rice", "#fff7ed", "#fee2e2", False, "Egg Curry &amp; Rice", "Hard-Boiled Eggs in Rich Masala &amp; Rice",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="115" rx="82" ry="50" fill="#cbd5e1" />
        <ellipse cx="200" cy="115" rx="76" ry="44" fill="#ffffff" />
        <!-- Steamed Rice (Left) -->
        <path d="M128 115 C 128 90, 195 90, 200 115 C 200 140, 128 140, 128 115 Z" fill="#f8fafc" />
        <ellipse cx="160" cy="114" rx="30" ry="22" fill="#ffffff" />
        <!-- Spiced Egg Gravy (Right) -->
        <path d="M200 115 C 200 90, 268 90, 272 115 C 272 140, 200 140, 200 115 Z" fill="#c2410c" />
        <ellipse cx="236" cy="114" rx="32" ry="22" fill="#ea580c" />
        <!-- 2 Sliced Boiled Eggs with Bright Yolks -->
        <ellipse cx="225" cy="110" rx="14" ry="10" fill="#ffffff" stroke="#fed7aa" stroke-width="1" transform="rotate(-15 225 110)" />
        <circle cx="225" cy="110" r="6" fill="#facc15" />
        <ellipse cx="245" cy="120" rx="14" ry="10" fill="#ffffff" stroke="#fed7aa" stroke-width="1" transform="rotate(20 245 120)" />
        <circle cx="245" cy="120" r="6" fill="#facc15" />
        <!-- Coriander & Gravy Details -->
        <path d="M232 102 C 232 98, 237 98, 237 102 Z" fill="#15803d" />
        <circle cx="218" cy="118" r="2" fill="#15803d" />
        <!-- Steam -->
        <path d="M236 80 Q 242 66 236 52" stroke="rgba(234,88,12,0.5)" stroke-width="2.5" stroke-linecap="round" fill="none" />
        """
    )

    # 21. Default Cooked Meal
    svgs["default"] = make_svg(
        "default", "#f0fdf4", "#ecfdf5", True, "Wholesome Cooked Meal", "Fresh Prepared Food Ready for Community Pickup",
        """
        <ellipse cx="200" cy="170" rx="84" ry="18" fill="rgba(15,23,42,0.16)" />
        <ellipse cx="200" cy="120" rx="80" ry="46" fill="#cbd5e1" />
        <ellipse cx="200" cy="120" rx="74" ry="40" fill="#f8fafc" />
        <!-- Serving Cloche / Warm Casserole Base -->
        <path d="M140 120 C 140 156, 166 166, 200 166 C 234 166, 260 156, 260 120 Z" fill="#2563eb" />
        <ellipse cx="200" cy="120" rx="60" ry="22" fill="#3b82f6" />
        <!-- Warm Food Glow inside -->
        <ellipse cx="200" cy="118" rx="52" ry="17" fill="#f59e0b" />
        <ellipse cx="200" cy="118" rx="42" ry="13" fill="#fef08a" />
        <!-- Heart / Care Symbol Rising -->
        <path d="M200 95 C 190 75, 165 72, 165 92 C 165 110, 200 125, 200 125 C 200 125, 235 110, 235 92 C 235 72, 210 75, 200 95 Z" fill="#ef4444" opacity="0.9" />
        <!-- Rising Steam Wisps -->
        <path d="M182 66 Q 176 48 184 34" stroke="rgba(245,158,11,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M200 62 Q 194 44 200 30" stroke="rgba(239,68,68,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        <path d="M218 66 Q 224 48 216 34" stroke="rgba(245,158,11,0.6)" stroke-width="3" stroke-linecap="round" fill="none" />
        """
    )

    # Validate and write each SVG to both directories
    target_dirs = ["app/static/img/food", "static/img/food"]
    for d in target_dirs:
        os.makedirs(d, exist_ok=True)

    print(f"Total SVGs defined: {len(svgs)}")
    for key, content in svgs.items():
        # Validate XML well-formedness
        try:
            ET.fromstring(content)
        except Exception as e:
            print(f"ERROR in {key}: {e}")
            raise e

        # Write to both target directories
        filename = f"{key}.svg"
        for d in target_dirs:
            path = os.path.join(d, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
        print(f"OK: {filename}")

    print("All 21 SVGs generated and validated successfully!")

if __name__ == "__main__":
    generate_all_svgs()
