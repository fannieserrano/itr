import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import seaborn as sns

results_folder = "../Output/ar6wg3/"
subfolders = [
    "each/SSP1/IMAGE_3.0.1",
    "each/SSP2/IMAGE_3.0.1",
    "each/SSP3/IMAGE_3.0.1",
    "each/SSP4/IMAGE_3.0.1",
    "each/SSP5/IMAGE_3.0.1",
    "each/SSP1/IMAGE_3.2",
    "each/SSP2/IMAGE_3.2",
    "each/SSP2/MESSAGEix-GLOBIOM_GEI",
    "each/SSP1/AIM_CGE_2.0",
    "each/SSP2/MESSAGE-GLOBIOM_1.0",
    "each/SSP3/MESSAGE-GLOBIOM_1.0",
    "each/SSP4/AIM_CGE_2.0",
    "each/SSP5/REMIND-MAgPIE_1.5",
]

# The results will go into the output folder, in this subfolder:
plot_folder = "../Output/Plots/each/"
if not os.path.exists(results_folder + plot_folder):
    os.makedirs(results_folder + plot_folder)

# Files to read will have this basic structure:
file_format ="{}normal_magicc_{}_fair_{}_esf_7.1pm26.7_likeli_0.6827_nonCO2pc50_GtCO2_permaf_False_zecsd_0.19_asym_False_hdT_1.07NonlinNonCO2_{}_{}_recEm209.csv"
cols = ["Database", "NonCO2"]
historic_warming = 1.07
results_table = pd.DataFrame(
    columns=cols
)
magicc0 = True
fair0 = True
peak0 = "nonCO2AtPeakTot"
nonco20 = "interp"
baseline_file = file_format.format("budget_", magicc0, fair0, nonco20, peak0)
results = pd.read_csv(
    results_folder + baseline_file
)
for col, res in [
    ("Database", "AR6"),
    ("MAGICC", magicc0),
    ("FaIR", fair0),
    ("NonCO2", nonco20),
]:
    results[col] = res
results_table = results
for subfolder in subfolders:
    for MAGICC in [magicc0]:
        for FaIR in [fair0]:
            for NonCO2 in ["interp"]:
                try:
                    filename = file_format.format(
                        subfolder, MAGICC, FaIR, NonCO2, peak0
                    )
                    results = pd.read_csv(
                        results_folder + filename
                    )
                except FileNotFoundError:
                    print("Didn't find " + filename)
                    continue

                for col, res in [
                    ("Database", subfolder),
                    ("MAGICC", MAGICC),
                    ("FaIR", FaIR),
                    ("NonCO2", NonCO2)
                ]:
                    results[col] = res
                results_table = results_table.append(results)
results_table = results_table.reset_index(drop=True)
if not os.path.exists(plot_folder):
    os.makedirs(plot_folder)
results_table.to_csv(plot_folder + "model_specific_summary.csv")
results_table["Scenario"] = [x[5: 9] if len(x) > 3 else "All AR6" for x in results_table["Database"]]
results_table["Model"] = [x[10:] if len(x) > 3 else "All AR6" for x in results_table["Database"]]

temp = 1.5
quantiles = ["0.17", "0.33","0.5", "0.66", "0.83"]
to_plot = results_table.melt(
    var_name="Quantile", value_name="Budget", value_vars=quantiles, id_vars=["dT_targets", "Scenario", "Model"]
)
to_plot = to_plot.loc[
    np.isclose(to_plot["dT_targets"], temp),
    :
]
plt.close()
sns.catplot(
    data=to_plot, x="Scenario", hue="Model", y="Budget", kind="box",
)
plt.savefig(plot_folder + "scenario_budgets_catplot.png")

# Plot different peak/non-CO2 waring of scenario families on the same plot
magicc_db = pd.read_csv(
    results_folder + "magicc_nonCO2_temp_50PercentilenonCO2AtPeakTotpermaf_False.csv"
)
fair_db = pd.read_csv(
    results_folder + "fair_nonCO2_temp_50Percentile_nonCO2AtPeakTot.csv"
)
fair_db = fair_db.set_index("magicc_ind")
magicc_non_co2_col = (
    "non-co2 warming (rel. to 2010-2019) at peak cumulative emissions co2"
)
magicc_temp_col = "peak surface temperature (rel. to 2010-2019)"
master_all_non_co2 = pd.DataFrame(
    index=magicc_db.index,
    columns=[magicc_non_co2_col, magicc_temp_col]
)
master_all_non_co2[magicc_non_co2_col] = (fair_db[
    magicc_non_co2_col] + magicc_db.reset_index()[magicc_non_co2_col]) / 2
master_all_non_co2[magicc_temp_col] = (fair_db[
     magicc_temp_col] + magicc_db.reset_index()[magicc_temp_col]) / 2
master_all_non_co2.index = magicc_db.index
master_all_non_co2["Scenario"] = magicc_db["scenario"]
master_all_non_co2["Model"] = magicc_db["model"]

image_data = master_all_non_co2.loc[master_all_non_co2["Model"] == "IMAGE 3.0.1"]
legends = []
plt.close()
for scenario in ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]:
    ind = [x[:len(scenario)] == scenario for x in image_data["Scenario"]]
    plt.plot(historic_warming + image_data[magicc_temp_col].iloc[ind],
        image_data[magicc_non_co2_col].iloc[ind]
    )
    legends.append(scenario)
plt.legend(legends)
plt.xlabel("Peak total warming (C)")
plt.ylabel("Non-CO$_2$ warming relative to 2010-2019 (C)")
plt.savefig(plot_folder + "IMAGE_3.0.1_ssps.png")