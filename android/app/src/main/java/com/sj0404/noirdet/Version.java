package com.sj0404.noirdet;

/** Числовое сравнение версий из тегов вида v0.10.0 (не строковое!). */
public final class Version {

    private Version() {}

    private static int[] parse(String tag) {
        int[] v = new int[3];
        if (tag == null || tag.isEmpty()) return v;
        String s = tag.trim();
        if (s.length() > 0 && (s.charAt(0) == 'v' || s.charAt(0) == 'V')) s = s.substring(1);
        int i = 0;
        int part = 0;
        while (i <= s.length() && part < 3) {
            int j = i;
            while (j < s.length() && Character.isDigit(s.charAt(j))) j++;
            if (j == i) break;
            v[part] = Integer.parseInt(s.substring(i, j));
            part++;
            i = j;
            while (i < s.length() && (s.charAt(i) == '.' || s.charAt(i) == '-')) i++;
        }
        return v;
    }

    /**
     * @return &gt;0 если a больше b, &lt;0 если a меньше, 0 — равны
     */
    public static int compare(String a, String b) {
        int[] va = parse(a);
        int[] vb = parse(b);
        for (int i = 0; i < 3; i++) {
            if (va[i] != vb[i]) return va[i] - vb[i];
        }
        return 0;
    }
}