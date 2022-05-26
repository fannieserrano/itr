import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns

results_folder = "../Output/"
subfolders = ["sr15wg1/", "ar6wg3/", "sr15ccbox71/"]

# The results will go into the output folder, in this subfolder:
plot_folder = "Plots/"
if not os.path.exists(results_folder + plot_folder):
    os.makedirs(results_folder + plot_folder)

# If plot_distn is "allquant" we plot the effect of the TCRE distribution on results.
# If the empty string, we plot the impact
plot_distn = ""
# Files to read will have this basic structure:
file_format = plot_distn + "budget_{}_magicc_{}_fair_{}_esf_{}pm26.7_likeli_0.6827_" \
              "nonCO2pc50_GtCO2_permaf_{}_zecsd_{}_asym_{}_hdT_1.07NonlinNonCO2_{}_None_recEm209.csv"
cols = ["Database", "TCRE Distribution", "MAGICC", "FaIR", "ESF", "Permafrost", "ZECsd", "ZEC asymmetry","NonCO2"]
results_table = pd.DataFrame(
    columns=cols
)
for subfolder in subfolders:
    for distribution in ["normal", "lognormal"]:
        for MAGICC in [True, False]:
            for FaIR in [True, False]:
                for ESF in [7.1]:
                    for Permafrost in [True, False]:
                        for NonCO2 in ["all", "QRW"]:
                            for zecsd in ["0.0", "0.19"]:
                                for zecasym in [True, False]:
                                    try:
                                        filename = file_format.format(
                                            distribution, MAGICC, FaIR, ESF,
                                            Permafrost, zecsd, zecasym, NonCO2
                                        )
                                        results = pd.read_csv(
                                            results_folder + subfolder + filename
                                        )
                                    except FileNotFoundError:
                                        print("Didn't find " + filename)
                                        continue

                                    for col, res in [
                                        ("Database", subfolder[:-1].upper()),
                                        ("TCRE Distribution", distribution),
                                        ("MAGICC", MAGICC),
                                        ("FaIR", FaIR),
                                        ("ESF", ESF),
                                        ("Permafrost", Permafrost),
                                        ("ZECsd", zecsd),
                                        ("ZEC asymmetry", zecasym),
                                        ("NonCO2", NonCO2)
                                    ]:
                                        results[col] = res
                                    results_table = results_table.append(results)
results_table = results_table.reset_index(drop=True)

# Put in some defaults
d0 = "AR6WG3"
ESF0 = 7.1
zec_sd0 = "0.19"
p0 = False
as0 = False
NonCO20 = "all"

if not plot_distn:
    for nonco2 in ["all", "QRW"]:
        for futwarm in [0.43, 0.93]:
            plt.close()
            use_results = results_table.loc[
                ([r in ["SR15CCBOX71", "SR15WG1"] for r in results_table["Database"]]) & (
                np.isclose(results_table["Future_warming"], futwarm)) & (
                results_table["TCRE Distribution"]=="normal") & (results_table["Permafrost"] == False) & (
                results_table["ESF"] == 7.1) & (results_table["NonCO2"] == nonco2),
                :
            ]
            use_results["Updated"] = ["yes" if y == "SR15CCBOX71" else "no" for y in use_results["Database"]]
            use_results["Model"] = "MAGICC"
            use_results.loc[~use_results["MAGICC"].astype(bool), "Model"] = "FaIR"
            use_results.loc[use_results["MAGICC"] & use_results["FaIR"], "Model"] = "MAGICC and FaIR"
            use_results = use_results.melt(
                var_name="Quantile",
                value_name="Budget",
                value_vars=["0.17", "0.33", "0.5", "0.66", "0.83"],
                id_vars=cols + ["Updated", "Model"]
            )

            sns.catplot(
                data=use_results, x="Model", hue="Updated", y="Budget", kind="box", hue_order=["no", "yes"]
            )
            plt.savefig(
                results_folder + plot_folder + f"updates_Distn_ftwarm{futwarm}_nonco2_{nonco2}.png")

    # Calculate fractional change caused by some modifications
    compare = []
    quant_dict = {0.43: "0.5", 0.93: "0.66"}
    hist_warm = 1.07
    for futwarm in [0.43, 0.93]:
        basebool = pd.DataFrame({
            "Database": (results_table["Database"] == d0),
            "Future_warming": np.isclose(results_table["Future_warming"], futwarm),
            "SCM": results_table["MAGICC"] & results_table["FaIR"],
            "ESF": (results_table["ESF"] == ESF0),
            "Permafrost": (results_table["Permafrost"] == p0),
            "ZECsd": (results_table["ZECsd"] == zec_sd0),
            "ZEC asymmetry": (results_table["ZEC asymmetry"] == as0),
            "NonCO2": (results_table["NonCO2"] == NonCO20)
        })

        baseline = results_table.iloc[
            [bool(x) for x in np.product(basebool, axis=1)]
        ]
        assert len(baseline) == 1
        db = results_table.iloc[
            [bool(x) for x in (np.product(basebool.iloc[:, 1:], axis=1) &
                               (results_table["Database"] == "SR15CCBOX71"))]
        ]
        assert len(db) == 1
        compare.append(
            [futwarm + hist_warm, quant_dict[futwarm], "Database", (
                (db[quant_dict[futwarm]].values - baseline[quant_dict[futwarm]].values) /
                baseline[quant_dict[futwarm]].values
            )[0]]
        )
        pf = results_table.iloc[
            [bool(x) for x in (np.product(basebool.iloc[:, :4], axis=1) &
                               np.product(basebool.iloc[:, 5:], axis=1) &
                               (results_table["Permafrost"] == True))]
        ]
        assert len(pf) == 1
        compare.append(
            [futwarm + hist_warm, quant_dict[futwarm], "Permafrost",
             ((pf[quant_dict[futwarm]].values - baseline[quant_dict[futwarm]].values) / baseline[
                 quant_dict[futwarm]].values)[0]
             ]
        )
        ZECsd = results_table.iloc[
            [bool(x) for x in (np.product(basebool.iloc[:, :5], axis=1) &
                               np.product(basebool.iloc[:, 6:], axis=1) &
                               (results_table["ZECsd"] == "0.0"))]
        ]
        assert len(ZECsd) == 1
        compare.append(
            [futwarm + hist_warm, quant_dict[futwarm], "ZEC sd",
             ((ZECsd[quant_dict[futwarm]].values - baseline[quant_dict[futwarm]].values) /
              baseline[
                  quant_dict[futwarm]].values)[0]]
        )
        ZECas = results_table.iloc[
            [bool(x) for x in (np.product(basebool.iloc[:, :6], axis=1) &
                               np.product(basebool.iloc[:, 7:], axis=1) &
                               (results_table["ZEC asymmetry"] == True))]
        ]
        assert len(ZECas) == 1
        compare.append(
            [futwarm + hist_warm, quant_dict[futwarm], "ZEC asymmtetry",
             ((ZECas[quant_dict[futwarm]].values - baseline[quant_dict[futwarm]].values) / baseline[
                 quant_dict[futwarm]].values)[0] ]
        )
        NonCO2 = results_table.iloc[
            [bool(x) for x in (np.product(basebool.iloc[:, :-2], axis=1) &
                               (results_table["NonCO2"] == "QRW"))]
        ]
        assert len(NonCO2) == 1
        compare.append(
            [futwarm + hist_warm, quant_dict[futwarm], "NonCO2",
             ((NonCO2[quant_dict[futwarm]].values - baseline[quant_dict[futwarm]].values) /
              baseline[
                  quant_dict[futwarm]].values)[0]]
        )

    comparedf = pd.DataFrame(
        compare, columns=["Warming", "Quantile", "Change", "Percentage change"]
    )
    comparedf["Percentage change"] = [round(100 * x, 2) for x in comparedf["Percentage change"]]
    comparedf.to_csv(results_folder + "impact_of_changes.csv")

if plot_distn:
    for futwarm in [0.43, 0.93]:
        plt.close()
        use_results = results_table.loc[
            (results_table["Database"] == d0) &
            (results_table["ESF"] == ESF0) &
            (results_table["Permafrost"] == p0) &
            np.isclose(results_table["Future_warming"], futwarm) &
            (results_table["MAGICC"]) & (results_table["FaIR"] == False) &
            (results_table["ZECsd"]==zec_sd0) &
            (results_table["NonCO2"] == NonCO20),
            :
        ]
        use_results = use_results.set_index(cols + ["Future_warming", "dT_targets"])
        use_results.columns = [str(round(float(c), 4)) for c in use_results.columns]
        use_results = use_results.sort_index(axis=1)

        use_results = use_results.reset_index().melt(
            var_name="Quantile",
            value_name="Budget",
            value_vars=[str(round(x, 4)) for x in np.arange(0.01, 0.991, 0.0025)],
            id_vars=cols
        )
        sns.set_theme(style="whitegrid")
        sns.violinplot(
            data=use_results, x="TCRE Distribution", hue="ZEC asymmetry",
            y="Budget", cut=0, split=True, bw=0.3, inner="quartile",
        )
        plt.savefig(results_folder + plot_folder + f"violinplot_TCREZECDistn_ftwarm{futwarm}.png")
